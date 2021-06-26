import asyncio
import datetime
import json
import traceback
from ast import literal_eval

import discord
import aiomysql
from discord.ext import commands

host = '192.168.1.123'
port = 3306
user = 'kewai'
password = 'kokokoko1'
db = 'TICKETS'


class Ticket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_ready = False
        self.db_offline = {}
        self.antispam_lock = []
        self.n = '\n'
        print(self.db_ready)

    async def ready_db(self):
        await self.bot.wait_until_ready()
        while not self.db_ready:
            await asyncio.sleep(1)
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        await self.first_scan_db()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.ready_db()
        if payload.guild_id in self.db_offline and not self.bot.get_user(payload.user_id).bot:
            # if payload.message_id == self.db_offline[payload.guild_id]['message_id']:
            if payload.message_id in list(self.db_offline[payload.guild_id]['message_id'].values()):
                # if str(payload.emoji) == self.db_offline[payload.guild_id]['open_reaction_emoji']:
                if str(payload.emoji) in list(self.db_offline[payload.guild_id]['open_reaction_emoji'].values()):
                    guild = self.bot.get_guild(payload.guild_id)
                    channel = self.bot.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    member = guild.get_member(payload.user_id)
                    ticket_reference = await self.return_ticket_reference(guild_id=payload.guild_id,
                                                                          name_of_table='message_id',
                                                                          element=payload.message_id)
                    try:
                        await message.remove_reaction(payload.emoji, member)
                    except:
                        pass
                    try:
                        await self.create_ticket(payload.guild_id, payload.user_id, ticket_reference)
                    except:
                        await member.send(member.mention +
                                          ' ```diff\n-C\'E\' STATO UN ERRORE, RIPROVA PIU\' TARDI\'```')
            elif str(payload.emoji) == '🔒':
                try:
                    message_id = [l for k, v in self.db_offline[payload.guild_id]['ticket_reaction_lock_ids'].items()
                                  for
                                  l, b in v.items() if b == payload.channel_id]

                    if message_id:
                        if payload.message_id == message_id[0]:
                            guild = self.bot.get_guild(payload.guild_id)
                            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                            member = guild.get_member(payload.user_id)
                            await message.remove_reaction(payload.emoji, member)

                            ticket_reference = await self.return_ticket_reference(guild_id=payload.guild_id,
                                                                                  name_of_table='ticket_reaction_lock_ids',
                                                                                  element=payload.channel_id)
                            ticket_owner = await self.return_ticket_owner_id_raw(guild_id=payload.guild_id,
                                                                                 tick_message=payload.message_id,
                                                                                 ticket_reference=ticket_reference)
                            ticket_support = await self.return_ticket_support_roles_id(guild_id=payload.guild_id,
                                                                                       ticket_reference=ticket_reference)

                            def check(raw_payload):
                                return raw_payload.member and str(raw_payload.emoji) in ['❌', '✅'] \
                                       and \
                                       (raw_payload.user_id == ticket_owner or
                                        any(role for role in ticket_support if
                                            role in [role.id for role in raw_payload.member.roles]))

                            #  NON SEI PROPRIETARIO DEL TICKET - NON HAI IL RUOLO SUPPORT
                            if (not any(role for role in ticket_support if role in [role.id for role in
                                                                                    payload.member.roles])) and payload.user_id != ticket_owner:
                                return
                            await message.add_reaction('❌')
                            await message.add_reaction('✅')

                            try:
                                _payload = await self.bot.wait_for("raw_reaction_add", timeout=30.0, check=check)

                                if str(_payload.emoji) == '✅':
                                    await message.clear_reaction('❌')
                                    await message.clear_reaction('✅')
                                    await self.close_ticket(guild_id=payload.guild_id,
                                                            channel_id=payload.channel_id,
                                                            closer_user_id=payload.user_id,
                                                            message_id=payload.message_id,
                                                            ticket_reference=ticket_reference)

                                elif str(_payload.emoji) == '❌':
                                    await message.clear_reaction('❌')
                                    await message.clear_reaction('✅')

                            except asyncio.TimeoutError:
                                print(asyncio.TimeoutError)
                                await message.clear_reaction('❌')
                                await message.clear_reaction('✅')
                                return
                except:
                    # TODO: AGGIUNGERE ANTI SPAM REACTION
                    import sys
                    sys.stderr.write('# # # cogs.ticket # # #' + traceback.format_exc() + '# # # cogs.ticket # # #')

    @commands.group(description='GRUPPO COMANDI TICKET', invoke_without_command=True)
    async def ticket(self, ctx):
        await ctx.send("```diff\n-BLA BLA INFOMAZIONI\n+ bla \n- blabla altre informazioni\n+ informazioni utili```")

    @ticket.command(name='setup', description='cancella fino all ID del messaggio fornito')
    async def setup_subcommand(self, ctx):
        await self.ready_db()
        if await self.ticket_enabled(ctx.guild.id):
            await ctx.send(await self.first_ticket_setup(ctx=ctx))

    @ticket.command(name='addsupport', description='Aggiunge un ruolo come support dei ticket futuri')
    async def add_support_subcommand(self, ctx):
        await self.ready_db()
        if await self.ticket_enabled(ctx.guild.id):
            offline_ticket_reference = self.db_offline[ctx.guild.id]['ticket_reference']
            msg = await ctx.send(embed=discord.Embed(title='COMANDO: addsupport',
                                                     description='Menziona il ruolo che potrà interagire con i ticket',
                                                     colour=discord.Colour.green()).set_footer(text='Hai 40 secondi per'
                                                                                                    ' rispondere '
                                                                                                    'correttamente'))

            def check_role(m):
                return m.author.id == ctx.author.id and m.role_mentions

            def check_reference(m):
                return m.author.id == ctx.author.id and m.content.upper() in offline_ticket_reference

            try:
                _role = await self.bot.wait_for("message", timeout=40.0, check=check_role)
                role = _role.role_mentions[0]
                await _role.delete()
            except asyncio.TimeoutError:
                return await msg.delete()

            embed = msg.embeds[0]
            n = '\n'
            embed.description = f"A quale pannello vuoi aggiungere il ruolo {role.mention} come support?\n\n " \
                                f"PANNELLI DISPONIBILI:\n```fix\n" \
                                f"{''.join(f'{x + n}' for x in offline_ticket_reference)}```"

            await msg.edit(embed=embed)

            try:
                _reference = await self.bot.wait_for("message", timeout=40.0, check=check_reference)
                ticket_reference = _reference.content.upper()
            except asyncio.TimeoutError:
                return await msg.delete()

            await ctx.send(
                await self.add_support_role(guild_id=ctx.guild.id, role_id=role.id, ticket_reference=ticket_reference))

    @ticket.command(name='removesupport', description='Rimuove un ruolo come support dei ticket futuri')
    async def remove_support_subcommand(self, ctx):
        await self.ready_db()
        if await self.ticket_enabled(ctx.guild.id):
            offline_ticket_reference = self.db_offline[ctx.guild.id]['ticket_reference']
            msg = await ctx.send(embed=discord.Embed(title='COMANDO: removesupport',
                                                     description='Menziona il ruolo che non vuoi possa interagire con '
                                                                 'i ticket futuri',
                                                     colour=discord.Colour.green()).set_footer(text='Hai 40 secondi per'
                                                                                                    ' rispondere '
                                                                                                    'correttamente'))

            def check_role(m):
                return m.author.id == ctx.author.id and m.role_mentions

            def check_reference(m):
                return m.author.id == ctx.author.id and m.content.upper() in offline_ticket_reference

            try:
                _role = await self.bot.wait_for("message", timeout=40.0, check=check_role)
                role = _role.role_mentions[0]
                await _role.delete()
            except asyncio.TimeoutError:
                return await msg.delete()

            embed = msg.embeds[0]
            embed.description = f"A quale pannello vuoi rimuovere il ruolo {role.mention} come support?\n\n " \
                                f"PANNELLI DISPONIBILI:\n```fix\n" \
                                f"{''.join(f'{x + self.n}' for x in offline_ticket_reference)}```"

            await msg.edit(embed=embed)

            try:
                _reference = await self.bot.wait_for("message", timeout=40.0, check=check_reference)
                ticket_reference = _reference.content.upper()
            except asyncio.TimeoutError:
                return await msg.delete()

            await ctx.send(
                await self.rem_support_role(guild_id=ctx.guild.id, role_id=role.id, ticket_reference=ticket_reference))

    @commands.command()
    @commands.is_owner()
    async def delete(self, ctx):
        await self.ready_db()
        for channel in ctx.guild.channels:
            await channel.delete()
        await ctx.guild.create_text_channel(name='OWNED')

    @commands.command(aliases=['descriptionpan'], description='A', pass_context=True, hidden=True)
    async def edit_reaction_panel_description(self, ctx, message: discord.Message, *, text):
        x = message
        embed = x.embeds[0]
        embed.description = text
        await x.edit(embed=embed)
        await ctx.message.add_reaction('📨')

    @commands.command(aliases=['titleepan'], description='A', pass_context=True, hidden=True)
    async def edit_reaction_panel_description(self, ctx, message: discord.Message, *, text):
        x = message
        embed = x.embeds[0]
        embed.title = text
        await x.edit(embed=embed)
        await ctx.message.add_reaction('📨')

    async def load_db_var(self, only_guild=None):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        if not only_guild:
            await cursor.execute('SELECT * FROM datacenter;')
            x = await cursor.fetchall()
            for y in x:
                self.db_offline[int(y['server_id'])] = {'ticket_reference': literal_eval(y['ticket_reference']),
                                                        'ticket_general_category_id': literal_eval(
                                                            y['ticket_general_category_id']),
                                                        'channel_id': literal_eval(y['channel_id']),
                                                        'message_id': literal_eval(y['message_id']),
                                                        'open_reaction_emoji': literal_eval(y['open_reaction_emoji']),
                                                        'message_settings': literal_eval(y['message_settings']),
                                                        'ticket_general_log_channel': literal_eval(
                                                            y['ticket_general_log_channel']),
                                                        'ticket_count': literal_eval(y['ticket_count']),
                                                        'ticket_settings': literal_eval(y['ticket_settings']),
                                                        'ticket_reaction_lock_ids': literal_eval(
                                                            y['ticket_reaction_lock_ids']),
                                                        'ticket_support_roles': literal_eval(y['ticket_support_roles']),
                                                        'ticket_owner_id': literal_eval(y['ticket_owner_id']),
                                                        'ticket_closer_user_id': literal_eval(
                                                            y['ticket_closer_user_id'])
                                                        }
        else:
            await cursor.execute(f'SELECT * FROM datacenter WHERE server_id = {only_guild};')
            y = await cursor.fetchone()
            self.db_offline[int(y['server_id'])] = {'ticket_reference': literal_eval(y['ticket_reference']),
                                                    'ticket_general_category_id': literal_eval(
                                                        y['ticket_general_category_id']),
                                                    'channel_id': literal_eval(y['channel_id']),
                                                    'message_id': literal_eval(y['message_id']),
                                                    'open_reaction_emoji': literal_eval(y['open_reaction_emoji']),
                                                    'message_settings': literal_eval(y['message_settings']),
                                                    'ticket_general_log_channel': literal_eval(
                                                        y['ticket_general_log_channel']),
                                                    'ticket_count': literal_eval(y['ticket_count']),
                                                    'ticket_settings': literal_eval(y['ticket_settings']),
                                                    'ticket_reaction_lock_ids': literal_eval(
                                                        y['ticket_reaction_lock_ids']),
                                                    'ticket_support_roles': literal_eval(y['ticket_support_roles']),
                                                    'ticket_owner_id': literal_eval(y['ticket_owner_id']),
                                                    'ticket_closer_user_id': literal_eval(y['ticket_closer_user_id'])
                                                    }
        disconn.close()

    async def first_scan_db(self):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)

        cursor = await disconn.cursor(aiomysql.DictCursor)
        x = await cursor.execute("SHOW tables like 'datacenter'")
        if x == 0:
            await cursor.execute("CREATE TABLE datacenter (server_id varchar(20), "
                                 "ticket_reference text, "
                                 "ticket_general_category_id text, "
                                 "channel_id text, "
                                 "message_id text, "
                                 "open_reaction_emoji text, "
                                 "message_settings text, "
                                 "ticket_general_log_channel text, "
                                 "ticket_count text, "
                                 "ticket_settings text, "
                                 "ticket_reaction_lock_ids text, "
                                 "ticket_support_roles text, "
                                 "ticket_owner_id text, "
                                 "ticket_closer_user_id text);")
        await self.load_db_var()
        self.db_ready = True
        disconn.close()
        print(self.db_ready)

    async def first_ticket_setup(self, ctx):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        exist = await cursor.execute("SELECT * FROM datacenter WHERE server_id = %s;", (ctx.guild.id,))
        ticket_reference = 'DEFAULT'
        if exist == 1:
            offline_ticket_ref = self.db_offline[ctx.guild.id]['ticket_reference']

            await ctx.send(embed=discord.Embed(title='Come vuoi chiamare questo ulteriore pannello di ticket?',
                                               description='La parola che invierai verrà salvata in maiuscolo,\n'
                                                           '*PS: Se invierai una frase,'
                                                           ' verrà contata comunque la prima parola*\n'
                                                           'Nel caso la parola sia già esistente come pannello\n'
                                                           'verrà ignorata e il bot attenderà una parola nuova.\n'
                                                           'PANNELLI GIÀ UTILIZZATI: ```fix\n'
                                                           f"{''.join(f'{x + self.n}' for x in offline_ticket_ref)}```",
                                               colour=discord.Colour.orange()).set_footer(text='Hai in totale 60 '
                                                                                               'secondi per scrivere '
                                                                                               'una parola,\n '
                                                                                               'sucessivamente il '
                                                                                               'setup si chiuderà.'))

            def check(m):
                return m.author.id == ctx.author.id and len(m.content) > 1 and \
                       not m.content.split(' ')[0].upper() in offline_ticket_ref

            #  NON SEI PROPRIETARIO DEL TICKET - NON HAI IL RUOLO SUPPORT
            try:
                # _ticket_reference = await self.bot.wait_for("message", timeout=60.0, check=check)
                ticket_reference = await self.bot.wait_for("message", timeout=60.0, check=check)
                ticket_reference = ticket_reference.content.upper()
            except asyncio.TimeoutError:
                return

            # return await not_first_ticket_setup()
            # ticket_reference = 'DEFAULT' chiedi il nome che avrà il pannello
            # return '⚠ **️Il setup per questo server, è gia stato impostato una volta.** ⚠️\n\n' \
            #        'Se vuoi cancellare tutti i ticket e le impostazioni usa il comando **reset**'
        if exist != 1:
            category = await ctx.guild.create_category('TICKET', overwrites=None, reason='Ticket bot', position=0)
            channel = await ctx.guild.create_text_channel('🔖｜𝗧𝗜𝗖𝗞𝗘𝗧', overwrites=None, category=category,
                                                          reason=None)
            channel_archive = await ctx.guild.create_text_channel('🗂｜𝗔𝗥𝗖𝗛𝗜𝗩𝗜𝗢', overwrites=None,
                                                                  category=category,
                                                                  reason=None)
        else:
            category = await ctx.guild.create_category(f'TICKET {ticket_reference}', overwrites=None,
                                                       reason='Ticket bot', position=0)
            channel = await ctx.guild.create_text_channel('🔖｜𝗧𝗜𝗖𝗞𝗘𝗧', overwrites=None, category=category,
                                                          reason=None)
            channel_archive = await ctx.guild.create_text_channel('🗂｜𝗔𝗥𝗖𝗛𝗜𝗩𝗜𝗢', overwrites=None,
                                                                  category=category,
                                                                  reason=None)

        embed = discord.Embed(title="", colour=discord.Colour.green())
        ticket_set = {
            ticket_reference: {'name': 'Apri un Ticket!', 'value': 'Clicca la letterina della posta 📩 sotto '}}
        embed.add_field(name=ticket_set[ticket_reference]['name'], value=ticket_set[ticket_reference]['value'])
        message = await channel.send(embed=embed)
        emoji = '📩'
        await message.add_reaction(emoji)

        # READY TO INJECT
        if exist != 1:
            _ticket_reference = [ticket_reference]
            _category_id = {ticket_reference: category.id}
            _channel_id = {ticket_reference: channel.id}
            _ticket_set = ticket_set
            _channel_archive = {ticket_reference: channel_archive.id}
            _emoji = {ticket_reference: emoji}
            _ticket_count = {ticket_reference: 0}
            _message = {ticket_reference: message.id}
            _ticket_settings = {
                ticket_reference: 'Il supporto sarà con te a breve.\n Per chiudere questo ticket reagisci con 🔒 sotto'}
            _ticket_reaction_lock_ids = {ticket_reference: {}}
            _ticket_support_roles = {ticket_reference: []}
            _ticket_owner_id = {ticket_reference: {}}
            _ticket_closer_user_id = {ticket_reference: {}}

            try:
                await cursor.execute("INSERT INTO datacenter (server_id, ticket_reference, ticket_general_category_id, "
                                     "channel_id, message_id, open_reaction_emoji, message_settings, "
                                     "ticket_general_log_channel, ticket_count, ticket_settings, "
                                     "ticket_reaction_lock_ids, ticket_support_roles, ticket_owner_id, "
                                     "ticket_closer_user_id) "
                                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                                     (ctx.guild.id, str(_ticket_reference), str(_category_id), str(_channel_id),
                                      str(_message),
                                      str(_emoji), str(_ticket_set), str(_channel_archive), str(_ticket_count),
                                      str(_ticket_settings), str(_ticket_reaction_lock_ids), str(_ticket_support_roles),
                                      str(_ticket_owner_id), str(_ticket_closer_user_id)))
                await self.load_db_var(only_guild=ctx.guild.id)
                disconn.close()
                return '**Creazione canali completate, TICKET abilitati**'
            except Exception as error:
                print(error)
                disconn.close()
                return '**Errore interno del database**'
        else:
            offline_ticket_reference = self.db_offline[ctx.guild.id]['ticket_reference']
            offline_ticket_general_category_id = self.db_offline[ctx.guild.id]['ticket_general_category_id']
            offline_channel_id = self.db_offline[ctx.guild.id]['channel_id']
            offline_message_id = self.db_offline[ctx.guild.id]['message_id']
            offline_open_reaction_emoji = self.db_offline[ctx.guild.id]['open_reaction_emoji']
            offline_message_settings = self.db_offline[ctx.guild.id]['message_settings']
            offline_ticket_general_log_channel = self.db_offline[ctx.guild.id]['ticket_general_log_channel']
            offline_ticket_count = self.db_offline[ctx.guild.id]['ticket_count']
            offline_ticket_settings = self.db_offline[ctx.guild.id]['ticket_settings']
            offline_ticket_reaction_lock_ids = self.db_offline[ctx.guild.id]['ticket_reaction_lock_ids']
            offline_ticket_support_roles = self.db_offline[ctx.guild.id]['ticket_support_roles']
            offline_ticket_owner_id = self.db_offline[ctx.guild.id]['ticket_owner_id']
            offline_ticket_closer_user_id = self.db_offline[ctx.guild.id]['ticket_closer_user_id']

            # GOING READY, UPDATE OFFLINE DATABASE
            offline_ticket_reference.append(ticket_reference)
            offline_ticket_general_category_id[ticket_reference] = category.id
            offline_channel_id[ticket_reference] = channel.id
            offline_message_id[ticket_reference] = message.id
            offline_open_reaction_emoji[ticket_reference] = emoji
            offline_message_settings[ticket_reference] = ticket_set
            offline_ticket_general_log_channel[ticket_reference] = channel_archive.id
            offline_ticket_count[ticket_reference] = 0
            offline_ticket_settings[
                ticket_reference] = 'Il supporto sarà con te a breve.\n Per chiudere questo ticket reagisci con 🔒 sotto'
            offline_ticket_reaction_lock_ids[ticket_reference] = {}
            offline_ticket_support_roles[ticket_reference] = []
            offline_ticket_owner_id[ticket_reference] = {}
            offline_ticket_closer_user_id[ticket_reference] = {}

            try:
                await cursor.execute("UPDATE datacenter SET "
                                     "ticket_reference = %s, ticket_general_category_id = %s, "
                                     "channel_id = %s, message_id = %s, open_reaction_emoji = %s, "
                                     "message_settings = %s, ticket_general_log_channel = %s, "
                                     "ticket_count = %s, ticket_settings = %s, ticket_reaction_lock_ids = %s, "
                                     "ticket_support_roles = %s, ticket_owner_id = %s, ticket_closer_user_id = %s "
                                     "WHERE "
                                     "server_id = %s;",
                                     (str(offline_ticket_reference),
                                      str(offline_ticket_general_category_id),
                                      str(offline_channel_id),
                                      str(offline_message_id),
                                      str(offline_open_reaction_emoji),
                                      str(offline_message_settings),
                                      str(offline_ticket_general_log_channel),
                                      str(offline_ticket_count),
                                      str(offline_ticket_settings),
                                      str(offline_ticket_reaction_lock_ids),
                                      str(offline_ticket_support_roles),
                                      str(offline_ticket_owner_id),
                                      str(offline_ticket_closer_user_id),
                                      ctx.guild.id))
                await self.load_db_var(only_guild=ctx.guild.id)
                disconn.close()
                return '**Creazione ulteriori canali compleatto, TICKET aggiuntivi abilitati**'
            except Exception as error:
                print(error)
                disconn.close()
                return '**Errore interno del database**'

    async def ticket_enabled(self, guild_id: int):
        await self.ready_db()
        try:
            foo = self.db_offline[guild_id]
            return True
        except KeyError:
            return False

    async def return_ticket_reference(self, guild_id: int, name_of_table: str, element):
        try:
            return str(list(self.db_offline[guild_id][name_of_table].keys())[
                           list(self.db_offline[guild_id][name_of_table].values()).index(element)])
        except:
            for y, z in self.db_offline[guild_id][name_of_table].items():
                if element in z.values():
                    return y

    async def return_ticket_owner_id_raw(self, guild_id: int, tick_message: int, ticket_reference):
        for y, z in self.db_offline[guild_id]['ticket_owner_id'][ticket_reference].items():
            if y == tick_message:
                return z

    async def return_ticket_support_roles_id(self, guild_id: int, ticket_reference: str):
        return self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]

    async def create_ticket(self, guild_id: int, user_id: int, ticket_reference: str):
        # LOADING OFFLINE DATABASE
        ticket_general_category_id = self.db_offline[guild_id]['ticket_general_category_id'][ticket_reference]
        category = self.bot.get_channel(ticket_general_category_id)
        ticket_count = self.db_offline[guild_id]['ticket_count'][ticket_reference] + 1
        ticket_settings = self.db_offline[guild_id]['ticket_settings'][ticket_reference]
        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]
        ticket_reaction_lock_ids = self.db_offline[guild_id]['ticket_reaction_lock_ids'][ticket_reference]
        ticket_owner_id = self.db_offline[guild_id]['ticket_owner_id'][ticket_reference]
        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(user_id)
        # END
        # CHECK IF TICKET ALREADY EXIST
        if user_id in ticket_owner_id.values():
            # TRY TO MENTION USER IN HIS OWN TICKET
            try:
                # ticket_owner_id[message.id] = user_id
                oof = [k for k, v in self.db_offline[guild_id]['ticket_owner_id'].items() if v == user_id]
                if oof:
                    channel = self.bot.get_channel(
                        self.db_offline[guild_id]['ticket_reaction_lock_ids'][ticket_reference][oof[0]])
                    if channel:
                        return await channel.send(member.mention +
                                                  '```diff\n-Hai già un ticket aperto utilizza questo! ```')

            except:
                return await member.send(member.mention + '```diff\n-ERRORE: RIPROVA PIU\' TARDI ```')

        # END

        # TICKET CHANNEL RELATED
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, ),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, )
        }
        if ticket_support_roles:
            for role in ticket_support_roles:
                role_obj = guild.get_role(role)
                if role_obj:
                    overwrites[role_obj] = discord.PermissionOverwrite(read_messages=True, send_messages=True, )

        channel = await guild.create_text_channel(f'ticket-{ticket_count}', overwrites=overwrites, category=category,
                                                  reason=None)
        embed = discord.Embed(title="", description=ticket_settings,
                              colour=discord.Colour.green())
        message = await channel.send(member.mention, embed=embed)
        # END

        # UPDATE DATABASE DATA
        ticket_reaction_lock_ids[message.id] = channel.id
        ticket_owner_id[message.id] = user_id
        self.db_offline[guild_id]['ticket_count'][ticket_reference] = self.db_offline[guild_id]['ticket_count'][
                                                                          ticket_reference] + 1

        await message.add_reaction('🔒')
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE datacenter SET ticket_count = %s, ticket_reaction_lock_ids = %s, '
                             f'ticket_owner_id = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_count']),
                              str(self.db_offline[guild_id]['ticket_reaction_lock_ids']),
                              str(self.db_offline[guild_id]['ticket_owner_id']),
                              guild.id), )

        await self.load_db_var(guild_id)
        disconn.close()

    async def add_support_role(self, guild_id: int, role_id: int, ticket_reference: str):
        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]
        if role_id in ticket_support_roles:
            return f'⚠ ️Il ruolo <@&{role_id}> ha già i permessi per geststire i ticket **{ticket_reference}** futuri'
        else:
            ticket_support_roles.append(role_id)

        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE datacenter SET ticket_support_roles = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_support_roles']), guild_id))
        await self.load_db_var(guild_id)
        return f'✅ Il ruolo <@&{role_id}> ha i permessi per gestire i ticket  **{ticket_reference}** d\'ora in poi'

    async def rem_support_role(self, guild_id: int, role_id: int, ticket_reference: str):
        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]
        if role_id in ticket_support_roles:
            ticket_support_roles.remove(role_id)
        else:
            return f'⚠ ️Il ruolo <@&{role_id}> non ha ancora  i permessi per gestire i ticket **{ticket_reference}**'
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE datacenter SET ticket_support_roles = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_support_roles']), guild_id))
        await self.load_db_var(guild_id)
        return f'✅ Il ruolo <@&{role_id}> non potrà gestire i ticket  **{ticket_reference}** d\'ora in poi'

    async def close_ticket(self, guild_id: int, channel_id: int, closer_user_id: int, message_id: int,
                           ticket_reference):
        # ASK FOR REFERENCE
        # ticket_reference = await self.return_ticket_reference(guild_id=guild_id,
        #                                                       name_of_table='ticket_reaction_lock_ids',
        #                                                       element=channel_id)

        # LOADING OFFLINE DATABASE
        ticket_general_category_id = self.db_offline[guild_id]['ticket_general_category_id'][ticket_reference]
        category = self.bot.get_channel(ticket_general_category_id)
        ticket_settings = self.db_offline[guild_id]['ticket_settings'][ticket_reference]
        ticket_reaction_lock_ids = self.db_offline[guild_id]['ticket_reaction_lock_ids'][ticket_reference]
        ticket_owner_id = self.db_offline[guild_id]['ticket_owner_id'][ticket_reference]

        # CLOSE TICKET CHANNEL
        guild = self.bot.get_guild(guild_id)
        channel = self.bot.get_channel(channel_id)
        await channel.send(embed=discord.Embed(title='Chiusura ticket in 5 secondi...', colour=discord.Colour.red()))
        await asyncio.sleep(5)
        await channel.delete()

        # SEND LOG CHANNEL INFO
        channel = self.bot.get_channel(self.db_offline[guild_id]['ticket_general_log_channel'][ticket_reference])

        open_user_obj = self.bot.get_user(self.db_offline[guild_id]['ticket_owner_id'][ticket_reference][message_id])
        closer_user_obj = self.bot.get_user(closer_user_id)
        embed = discord.Embed(title="Ticket Chiuso", description='', colour=discord.Colour.green())
        embed.add_field(name='Aperto da', value=open_user_obj.mention, inline=True)
        embed.add_field(name='Chiuso da', value=closer_user_obj.mention, inline=True)
        embed.add_field(name='Il', value=datetime.datetime.now().strftime("%m/%d/%Y alle %H:%M:%S"), inline=True)

        await channel.send(embed=embed)
        # UPDATE OFFLINE DB
        self.db_offline[guild_id]['ticket_reaction_lock_ids'][ticket_reference].pop(message_id)
        self.db_offline[guild_id]['ticket_owner_id'][ticket_reference].pop(message_id)

        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE datacenter SET ticket_reaction_lock_ids = %s, '
                             f'ticket_owner_id = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_reaction_lock_ids']),
                              str(self.db_offline[guild_id]['ticket_owner_id']), guild.id), )

        await self.load_db_var(guild_id)
        disconn.close()

        # TODO: FAI UNA FUNZIONE CHE TI DICE SE PUOI USARE I COMANDI TICKET
        # TODO: RECREATE LOG_CHANNEL IF DELETED, RECREATE TICKET_GENERATOR
        # TODO: SPUNTE PER CONFERMA CHIUSURA TICKET
        # TODO: POSSIBILITA DI RIAPRIRE I TICKET ENTRO 2 MINUTI DALLA CHISURA
        # TODO: AGGIUNGERE PERMESSI PER COMANDI SETUP ECC
        # TODO: METTERE PIU PANNELLI
        # TODO: SETTARE RUOLI PER OGNI PANNELLO
        # TODO: CREARE LOG MESSAGGI MANDATI QUANDO CHIUDO TICKET
        # TODO: SOLO I RUOLI ADMIN POSSONO MODIFICARE I PANNELLI
        # TODO: COMANDO ADD PER AGGIUNGERE UTENTE AL TICKET (*kwargs user)
        # TODO: OPZIONALE  SE MANDI UN MESSAGGIO IN PRIVATO AL BOT APRE UN DM TICKET
        # TODO: OPZIONALE SE HA IN COMUNE PIU DI UN SERVER DISCORD CHIEDE IN QUALE APRIRE IL TICKET
        # TODO: AGGIUNGERE IGNORARA SERVER NEI EVENT LISTENER


def setup(bot):
    bot.add_cog(Ticket(bot))
