import asyncio
import datetime
import json
import traceback
from ast import literal_eval

try:
    from data.config import *

    is_ciro_bot = True
except:
    is_ciro_bot = False
    print(is_ciro_bot)
import discord
import aiomysql
from discord.ext import commands, tasks

host = '192.168.1.123' if not is_ciro_bot else db_new_host
port = 3306 if not is_ciro_bot else db_new_port
user = 'kewai' if not is_ciro_bot else db_new_user
password = 'kokokoko1' if not is_ciro_bot else db_new_pass
db = 'TICKETS' if not is_ciro_bot else db_new_name


def translate_fronts(_string):
    dip = {
        'A': '𝗔',
        'B': '𝗕',
        'C': '𝗖',
        'D': '𝗗',
        'E': '𝗘',
        'F': '𝗙',
        'G': '𝗚',
        'H': '𝗛',
        'I': '𝗜',
        'L': '𝗟',
        'M': '𝗠',
        'N': '𝗡',
        'O': '𝗢',
        'P': '𝗣',
        'Q': '𝗤',
        'R': '𝗥',
        'S': '𝗦',
        'T': '𝗧',
        'U': '𝗨',
        'V': '𝗩',
        'Z': '𝗭',
        'X': '𝗫',
        'Y': '𝗬',
        'J': '𝗝',
        'K': '𝗞',
        'W': '𝗪',
        'Ì': 'Ì',
        'È': 'È',
        'É': 'É',
        'Ò': 'Ò',
        'À': 'À',
        'Ù': 'Ù',
    }
    return _string.translate(str.maketrans(dip))


class ticket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_ready = False
        self.db_offline = {}
        self.antispam_lock = []
        self.n = '\n'
        self._load_db.start()

    @tasks.loop(count=1)
    async def _load_db(self):
        await self.bot.wait_until_ready()
        await self.first_scan_db()

    async def ready_db(self):
        await self.bot.wait_until_ready()
        while not self.db_ready:
            await asyncio.sleep(1)
        return True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.ready_db()
        if payload.guild_id in self.db_offline and not self.bot.get_user(payload.user_id).bot:
            if payload.message_id in list(self.db_offline[payload.guild_id]['message_id'].values()):
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
                                                                                       ticket_reference=ticket_reference
                                                                                       )

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
                                    try:
                                        await message.clear_reaction('❌')
                                    except:
                                        pass
                                    try:
                                        await message.clear_reaction('✅')
                                    except:
                                        pass
                                    await self.close_ticket(guild_id=payload.guild_id,
                                                            channel_id=payload.channel_id,
                                                            closer_user_id=payload.user_id,
                                                            message_id=payload.message_id,
                                                            ticket_reference=ticket_reference)

                                elif str(_payload.emoji) == '❌':
                                    try:
                                        await message.clear_reaction('❌')
                                    except:
                                        pass
                                    try:
                                        await message.clear_reaction('✅')
                                    except:
                                        pass

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
        value = ''
        for c in self.bot.get_cog('ticket').get_commands():
            if not c.hidden:
                try:
                    if self.bot.get_command(c.name).commands:
                        for a in self.bot.get_command(c.name).commands:
                            value += f'`{c.name} {a.name}` - {a.description}\n'
                except:
                    import sys
                    sys.stderr.write('# # # cogs.ticket # # #' + traceback.format_exc() + '# # # cogs.ticket # # #')
        await ctx.send(value + 'TICKET IN BETA-TEST')

    @ticket.command(name='setup', description='Avvia la modalità di configurazione ticket')
    @commands.has_permissions(manage_messages=True)
    async def setup_subcommand(self, ctx):
        await self.ready_db()
        await ctx.send(await self.first_ticket_setup(ctx=ctx))

    @ticket.command(name='addsupport', description='Aggiunge un ruolo come support dei ticket futuri')
    @commands.has_permissions(manage_guild=True)
    async def add_support_subcommand(self, ctx):
        await self.ready_db()
        if await self.ticket_enabled(ctx.guild.id):
            offline_ticket_reference = self.db_offline[ctx.guild.id]['ticket_reference']
            msg = await ctx.send(embed=discord.Embed(title='COMANDO: addsupport',
                                                     description='Menziona i ruoli che potranno interagire con i ticket',
                                                     colour=discord.Colour.green()).set_footer(text='Hai 60 secondi per'
                                                                                                    ' rispondere '
                                                                                                    'correttamente'))

            def check_role(m):
                return m.author.id == ctx.author.id and m.role_mentions

            def check_reference(m):
                return m.author.id == ctx.author.id and m.content.upper() in offline_ticket_reference

            try:
                _role = await self.bot.wait_for("message", timeout=60.0, check=check_role)
                role = _role.role_mentions
                await _role.delete()
            except asyncio.TimeoutError:
                return await msg.delete()

            embed = msg.embeds[0]
            embed.description = f"A quale pannello vuoi aggiungere " \
                                f"{'il ruolo ' if len(role) == 1 else 'i ruoli '}" \
                                f"{' '.join([x.mention for x in role])}" \
                                f"come support?\n\n " \
                                f"PANNELLI DISPONIBILI:\n```fix\n" \
                                f"{''.join(f'{x + self.n}' for x in offline_ticket_reference)}```"

            await msg.edit(embed=embed)

            try:
                _reference = await self.bot.wait_for("message", timeout=40.0, check=check_reference)
                ticket_reference = _reference.content.upper()
            except asyncio.TimeoutError:
                return await msg.delete()

            await ctx.send(
                await self.add_support_role(guild_id=ctx.guild.id, roles=role, ticket_reference=ticket_reference))
        else:
            return await ctx.send(embed=discord.Embed(title='⚠ | Prima di utilizzare questo comando scrivi',
                                                      description='```fix\nticket setup```',
                                                      colour=discord.Colour.red()))

    @ticket.command(name='removesupport', description='Rimuove un ruolo come support dei ticket futuri')
    @commands.has_permissions(manage_guild=True)
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
                role = _role.role_mentions
                await _role.delete()
            except asyncio.TimeoutError:
                return await msg.delete()

            embed = msg.embeds[0]
            embed.description = f"A quale pannello vuoi rimuovere " \
                                f"{'il ruolo ' if len(role) == 1 else 'i ruoli '}" \
                                f"{' '.join([x.mention for x in role])}" \
                                f"come support?\n\n " \
                                f"PANNELLI DISPONIBILI:\n```fix\n" \
                                f"{''.join(f'{x + self.n}' for x in offline_ticket_reference)}```"

            await msg.edit(embed=embed)

            try:
                _reference = await self.bot.wait_for("message", timeout=40.0, check=check_reference)
                ticket_reference = _reference.content.upper()
            except asyncio.TimeoutError:
                return await msg.delete()

            await ctx.send(
                await self.rem_support_role(guild_id=ctx.guild.id, roles=role, ticket_reference=ticket_reference))
        else:
            return await ctx.send(embed=discord.Embed(title='⚠ | Prima di utilizzare questo comando scrivi',
                                                      description='```fix\nticket setup```',
                                                      colour=discord.Colour.red()))

    @ticket.command(name='edit', description='Ti permette di modificare le impostazioni per i ticket')
    @commands.has_permissions(manage_guild=True)
    async def edit_subcommand(self, ctx):
        await self.ready_db()
        if await self.ticket_enabled(ctx.guild.id):

            offline_ticket_ref = self.db_offline[ctx.guild.id]['ticket_reference']
            msg = await ctx.send(embed=discord.Embed(title='COMANDO: edit',
                                                     description='**Benvenuto nella modalita\' modifica,\n'
                                                                 'A quale pannello vuoi apportare modifiche?**\n'
                                                                 f'Pannelli disponibili:```fix\n'
                                                                 f"{''.join(f'{x + self.n}' for x in offline_ticket_ref)}```",
                                                     colour=discord.Colour.dark_grey())
                                 .set_footer(text='Hai 60 secondi per rispondere correttamente'))
            try:

                def check_reference(m):
                    return m.author.id == ctx.author.id and len(m.content) > 1 and \
                           m.content.split(' ')[0].upper() in offline_ticket_ref

                _ticket_reference = await self.bot.wait_for("message", timeout=60.0, check=check_reference)
                ticket_reference = _ticket_reference.content.upper()
                await _ticket_reference.delete()

                msg.embeds[0].description = f'**Cosa vorresti modificare nel pannello {ticket_reference}?**:\n' \
                                            '1️⃣= Formato del titolo dei ticket\n' \
                                            '2️⃣= Il pannello dove l\'utente apre il ticket\n' \
                                            '3️⃣= Il pannello che esce quando apri un ticket\n' \
                                            '4️⃣ = Abilita/Disabilita ticket multipli dalla stessa persona'
                msg.embeds[0].set_image(url='https://imgur.com/LmJSv6I.png')
                msg.embeds[0].colour = discord.Colour.green()

                await msg.edit(embed=msg.embeds[0])

                emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

                for x in emojis:
                    await msg.add_reaction(x)

                def check_choice(__reaction, __user):
                    return __user == ctx.author and str(__reaction.emoji) in emojis

                _reaction, _user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_choice)
                await msg.remove_reaction(_reaction, ctx.author)

                if str(_reaction.emoji) == '1️⃣':
                    # ENTRO NEL MENU MODIFICA TITOLO
                    msg.embeds[0].description = f"**MODIFICA TITOLO FUTURI TICKET**\n" \
                                                f"In che formato vorresti forsse il titolo dei ticket?\n" \
                                                f"1️⃣ = `ticket-176`\n" \
                                                f"2️⃣ = `ticket-aldo`\n" \
                                                f"3️⃣ = `176-aldo`\n" \
                                                f"4️⃣ = `176-aldo-{translate_fronts(ticket_reference)}`"
                    msg.embeds[0].set_image(url=discord.Embed.Empty)
                    await msg.edit(embed=msg.embeds[0])

                    _reaction, _user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_choice)
                    await msg.clear_reactions()

                    if str(_reaction.emoji) == '1️⃣':
                        await self.set_preferred_title_format(guild_id=ctx.guild.id,
                                                              ticket_reference=ticket_reference,
                                                              preference='ticket_number')
                    elif str(_reaction.emoji) == '2️⃣':
                        await self.set_preferred_title_format(guild_id=ctx.guild.id,
                                                              ticket_reference=ticket_reference,
                                                              preference='ticket_name')
                    elif str(_reaction.emoji) == '3️⃣':
                        await self.set_preferred_title_format(guild_id=ctx.guild.id,
                                                              ticket_reference=ticket_reference,
                                                              preference='number_name')
                    else:
                        await self.set_preferred_title_format(guild_id=ctx.guild.id,
                                                              ticket_reference=ticket_reference,
                                                              preference='number_name_reference')

                elif str(_reaction.emoji) == '2️⃣':
                    # ENTRO NEL MENU MODIFICA PANNELLO PRE TICKET
                    await msg.clear_reactions()

                    msg.embeds[0].description = f"Scrivi la frase che vuoi come **TITOLO** del pannello \n " \
                                                f"*(la frase che andrà al posto di \"Apri un Ticket!\")*"
                    msg.embeds[0].set_image(url='https://imgur.com/MGu2zmN.png')
                    await msg.edit(embed=msg.embeds[0])

                    def check_name(m):
                        return m.author == ctx.author and 256 > len(m.content) > 2

                    _name = await self.bot.wait_for("message", timeout=60.0, check=check_name)
                    name = _name.content
                    await _name.delete()

                    msg.embeds[0].description = f"Scrivi la frase che vuoi come **DESCRIZIONE** del pannello \n " \
                                                f"*(la frase che andrà al posto di \"Clicca la letterina della posta " \
                                                f":envelope_with_arrow: sotto)\" "

                    msg.embeds[0].colour = discord.Colour.orange()

                    await msg.edit(embed=msg.embeds[0])

                    def check_value(m):
                        return m.author == ctx.author and 1024 > len(m.content) > 2

                    _value = await self.bot.wait_for("message", timeout=120.0, check=check_value)
                    value = _value.content

                    await self.set_message_settings(guild_id=ctx.guild.id, ticket_reference=ticket_reference,
                                                    name=name, value=value)
                    await _value.delete()

                elif str(_reaction.emoji) == '3️⃣':
                    # ENTRO NEL MENU MODIFICA PANNELLO POST TICKET
                    await msg.clear_reactions()

                    msg.embeds[0].description = f"Scrivi la frase che vuoi come **contenuto** del pannello \n " \
                                                f"*(la frase che andrà al posto di \"" \
                                                f"Il supporto sarà con te a breve.\n " \
                                                f"Per chiudere questo ticket reagisci con 🔒 sotto\")*"

                    msg.embeds[0].set_image(url='https://imgur.com/a5ppSLr.png')

                    await msg.edit(embed=msg.embeds[0])

                    def check_description(m):
                        return m.author == ctx.author and 2048 > len(m.content) > 2

                    _description = await self.bot.wait_for("message", timeout=60.0, check=check_description)
                    description = _description.content
                    await _description.delete()

                    await self.set_ticket_settings(guild_id=ctx.guild.id, ticket_reference=ticket_reference,
                                                   description=description)

                else:
                    # ENTRO NEL MENU MODIFICA TICKET MULTIPLI
                    await msg.clear_reactions()
                    # ENTRO NEL MENU MODIFICA TITOLO
                    msg.embeds[0].description = f"**ABILITA / DISATTIVA TICKET MULTIPLI**\n" \
                                                f"Vuoi che un utente possa aprire più di un ticket nel pannello {translate_fronts(ticket_reference)}?\n"
                    msg.embeds[0].set_image(url=discord.Embed.Empty)
                    await msg.edit(embed=msg.embeds[0])
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')
                    emojis = ['✅', '❌']

                    _reaction, _user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_choice)

                    await msg.clear_reactions()

                    if str(_reaction.emoji) == '✅':
                        await self.set_ticket_multiple(guild_id=ctx.guild.id,
                                                       ticket_reference=ticket_reference,
                                                       preference=True)
                    elif str(_reaction.emoji) == '❌':
                        await self.set_ticket_multiple(guild_id=ctx.guild.id,
                                                       ticket_reference=ticket_reference,
                                                       preference=False)
                await msg.delete()
                await ctx.send('Impostazioni eseguite con successo.')
            except asyncio.TimeoutError:
                return await msg.delete()
        else:
            return await ctx.send(embed=discord.Embed(title='⚠ | Prima di utilizzare questo comando scrivi',
                                                      description='```fix\nticket setup```',
                                                      colour=discord.Colour.red()))

    @ticket.command(name='movepanel', description='Ti permette di spostare il pannello di reazione per i ticket')
    @commands.has_permissions(manage_guild=True)
    async def move_panel_subcommand(self, ctx):
        await self.ready_db()
        if await self.ticket_enabled(ctx.guild.id):
            offline_ticket_ref = self.db_offline[ctx.guild.id]['ticket_reference']
            msg = await ctx.send(embed=discord.Embed(title='COMANDO: movepanel',
                                                     description='**Benvenuto nella modalita\' movepanel,\n'
                                                                 'Quale pannello vuoi spostare di canale?**\n'
                                                                 f'Pannelli disponibili:```fix\n'
                                                                 f"{''.join(f'{x + self.n}' for x in offline_ticket_ref)}```",
                                                     colour=discord.Colour.dark_grey())
                                 .set_footer(text='Hai 60 secondi per rispondere correttamente'))
            try:
                def check_reference(m):
                    return m.author.id == ctx.author.id and len(m.content) > 1 and \
                           m.content.split(' ')[0].upper() in offline_ticket_ref

                _ticket_reference = await self.bot.wait_for("message", timeout=60.0, check=check_reference)
                ticket_reference = _ticket_reference.content.upper()
                await _ticket_reference.delete()

                msg.embeds[0].description = f'**Menziona il canale dove vuoi spostare il pannello {ticket_reference}**'
                msg.embeds[0].colour = discord.Colour.orange()
                await msg.edit(embed=msg.embeds[0])

                def check_channel(m):
                    return m.author.id == ctx.author.id and m.channel_mentions

                _channel = await self.bot.wait_for("message", timeout=60.0, check=check_channel)
                channel = _channel.channel_mentions[0]
                await _channel.delete()
                await self.move_ticket_message_settings(guild_id=ctx.guild.id,
                                                        ticket_reference=ticket_reference,
                                                        channel_destination=channel)
                await msg.delete()
                await ctx.send('Impostazioni eseguite con successo.')

            except asyncio.TimeoutError:
                return await msg.delete()
        else:
            return await ctx.send(embed=discord.Embed(title='⚠ | Prima di utilizzare questo comando scrivi',
                                                      description='```fix\nticket setup```',
                                                      colour=discord.Colour.red()))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def delete(self, ctx):
        await self.ready_db()
        for channel in ctx.guild.channels:
            await channel.delete()
        await ctx.guild.create_text_channel(name='TEST_SERVER')

    async def load_db_var(self, only_guild=None):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        if not only_guild:
            await cursor.execute('SELECT * FROM tickets_config;')
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
                                                            y['ticket_closer_user_id']),
                                                        'ticket_title_mode': literal_eval(y['ticket_title_mode']),
                                                        'ticket_multiple': literal_eval(y['ticket_multiple'])
                                                        }
        else:
            await cursor.execute(f'SELECT * FROM tickets_config WHERE server_id = {only_guild};')
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
                                                    'ticket_closer_user_id': literal_eval(y['ticket_closer_user_id']),
                                                    'ticket_title_mode': literal_eval(y['ticket_title_mode']),
                                                    'ticket_multiple': literal_eval(y['ticket_multiple'])
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
        x = await cursor.execute("SHOW tables like 'tickets_config'")
        if x == 0:
            await cursor.execute("CREATE TABLE tickets_config (server_id varchar(20), "
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
                                 "ticket_closer_user_id text,"
                                 "ticket_title_mode text,"
                                 "ticket_multiple text);")
        await self.load_db_var()
        self.db_ready = True
        disconn.close()

    async def first_ticket_setup(self, ctx):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        exist = await cursor.execute("SELECT * FROM tickets_config WHERE server_id = %s;", (ctx.guild.id,))
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

        if exist != 1:
            overwrites = await self.return_overwrites(guild=ctx.guild, everyone=True)
            category = await ctx.guild.create_category('TICKET', overwrites=None, reason='Ticket bot', position=0)
            channel = await ctx.guild.create_text_channel('🔖｜𝗧𝗜𝗖𝗞𝗘𝗧', overwrites=overwrites, category=category,
                                                          reason=None)
            overwrites = await self.return_overwrites(guild=ctx.guild, everyone=False)
            channel_archive = await ctx.guild.create_text_channel('🗂｜𝗔𝗥𝗖𝗛𝗜𝗩𝗜𝗢', overwrites=overwrites,
                                                                  category=category,
                                                                  reason=None)
        else:
            overwrites = await self.return_overwrites(guild=ctx.guild, everyone=True)
            category = await ctx.guild.create_category(f'TICKET {ticket_reference}', overwrites=None,
                                                       reason='Ticket bot', position=0)
            channel = await ctx.guild.create_text_channel('🔖｜𝗧𝗜𝗖𝗞𝗘𝗧', overwrites=overwrites, category=category,
                                                          reason=None)
            overwrites = await self.return_overwrites(guild=ctx.guild, everyone=False)
            channel_archive = await ctx.guild.create_text_channel('🗂｜𝗔𝗥𝗖𝗛𝗜𝗩𝗜𝗢', overwrites=overwrites,
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
            _ticket_title_mode = {ticket_reference: {'ticket_number': True,
                                                     'ticket_name': False,
                                                     'number_name': False,
                                                     'number_name_reference': False
                                                     }}
            _ticket_multiple = {ticket_reference: False}

            try:
                await cursor.execute(
                    "INSERT INTO tickets_config (server_id, ticket_reference, ticket_general_category_id, "
                    "channel_id, message_id, open_reaction_emoji, message_settings, "
                    "ticket_general_log_channel, ticket_count, ticket_settings, "
                    "ticket_reaction_lock_ids, ticket_support_roles, ticket_owner_id, "
                    "ticket_closer_user_id, ticket_title_mode, ticket_multiple) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                    (ctx.guild.id, str(_ticket_reference), str(_category_id), str(_channel_id),
                     str(_message),
                     str(_emoji), str(_ticket_set), str(_channel_archive), str(_ticket_count),
                     str(_ticket_settings), str(_ticket_reaction_lock_ids), str(_ticket_support_roles),
                     str(_ticket_owner_id), str(_ticket_closer_user_id), str(_ticket_title_mode),
                     str(_ticket_multiple)))
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
            offline_ticket_title_mode = self.db_offline[ctx.guild.id]['ticket_title_mode']
            offline_ticket_multiple = self.db_offline[ctx.guild.id]['ticket_multiple']

            # GOING READY, UPDATE OFFLINE DATABASE
            offline_ticket_reference.append(ticket_reference)
            offline_ticket_general_category_id[ticket_reference] = category.id
            offline_channel_id[ticket_reference] = channel.id
            offline_message_id[ticket_reference] = message.id
            offline_open_reaction_emoji[ticket_reference] = emoji
            offline_message_settings[ticket_reference] = {'name': 'Apri un Ticket!',
                                                          'value': 'Clicca la letterina della posta 📩 sotto '}
            offline_ticket_general_log_channel[ticket_reference] = channel_archive.id
            offline_ticket_count[ticket_reference] = 0
            offline_ticket_settings[
                ticket_reference] = 'Il supporto sarà con te a breve.\n Per chiudere questo ticket reagisci con 🔒 sotto'
            offline_ticket_reaction_lock_ids[ticket_reference] = {}
            offline_ticket_support_roles[ticket_reference] = []
            offline_ticket_owner_id[ticket_reference] = {}
            offline_ticket_closer_user_id[ticket_reference] = {}
            offline_ticket_title_mode[ticket_reference] = {'ticket_number': True,
                                                           'ticket_name': False,
                                                           'number_name': False,
                                                           'number_name_reference': False
                                                           }
            offline_ticket_multiple[ticket_reference] = False

            try:
                await cursor.execute("UPDATE tickets_config SET "
                                     "ticket_reference = %s, ticket_general_category_id = %s, "
                                     "channel_id = %s, message_id = %s, open_reaction_emoji = %s, "
                                     "message_settings = %s, ticket_general_log_channel = %s, "
                                     "ticket_count = %s, ticket_settings = %s, ticket_reaction_lock_ids = %s, "
                                     "ticket_support_roles = %s, ticket_owner_id = %s, ticket_closer_user_id = %s, "
                                     "ticket_title_mode = %s, ticket_multiple = %s "
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
                                      str(offline_ticket_title_mode),
                                      str(offline_ticket_multiple),
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

    async def set_preferred_title_format(self, guild_id: int, ticket_reference: str, preference: str):

        _ticket_title_mode = {
            'ticket_number': (True if preference == 'ticket_number' else False),
            'ticket_name': (True if preference == 'ticket_name' else False),
            'number_name': (True if preference == 'number_name' else False),
            'number_name_reference': (True if preference == 'number_name_reference' else False)
        }

        self.db_offline[guild_id]['ticket_title_mode'][ticket_reference] = _ticket_title_mode

        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE tickets_config SET ticket_title_mode = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_title_mode']), guild_id))
        await self.load_db_var(guild_id)

    async def set_ticket_multiple(self, guild_id: int, ticket_reference: str, preference: bool):
        self.db_offline[guild_id]['ticket_multiple'][ticket_reference] = preference

        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE tickets_config SET ticket_multiple = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_multiple']), guild_id))
        await self.load_db_var(guild_id)

    async def get_channel(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel
        else:
            # TODO: FEEDBACK PANNELLI ELIMINATI CANALI CATEGORIE ECC
            pass

    async def fetch_message(self, channel: discord.TextChannel, message_id: int):
        try:
            message = await channel.fetch_message(message_id)
            return message
        except:
            # TODO: FEEDBACK PANNELLI ELIMINATI CANALI CATEGORIE ECC
            pass

    async def set_message_settings(self, guild_id: int, ticket_reference: str, name: str, value: str):
        _message_settings = {'name': name, 'value': value}

        self.db_offline[guild_id]['message_settings'][ticket_reference] = _message_settings

        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE tickets_config SET message_settings = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['message_settings']), guild_id))
        await self.load_db_var(guild_id)

        channel = await self.get_channel(channel_id=self.db_offline[guild_id]['channel_id'][ticket_reference])
        if channel:
            message = await self.fetch_message(channel=channel,
                                               message_id=self.db_offline[guild_id]['message_id'][ticket_reference])
            message.embeds[0].set_field_at(0, name=name, value=value)
            # message.embeds[0].title = name
            # message.embeds[0].description = value
            await message.edit(embed=message.embeds[0])
            return True
        else:
            return False

    async def set_ticket_settings(self, guild_id: int, ticket_reference: str, description: str):
        self.db_offline[guild_id]['ticket_settings'][ticket_reference] = description

        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f'UPDATE tickets_config SET ticket_settings = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_settings']), guild_id))
        await self.load_db_var(guild_id)

        return True

    async def move_ticket_message_settings(self, guild_id: int, ticket_reference: str,
                                           channel_destination: discord.TextChannel):
        channel_id = self.db_offline[guild_id]['channel_id'][ticket_reference]
        message_id = self.db_offline[guild_id]['message_id'][ticket_reference]
        open_reaction_emoji = self.db_offline[guild_id]['open_reaction_emoji'][ticket_reference]

        channel = await self.get_channel(channel_id)
        if channel:
            message = await self.fetch_message(channel=channel, message_id=message_id)
            if message:
                await message.delete()

        offline_channel_id = self.db_offline[guild_id]['channel_id']
        offline_message_id = self.db_offline[guild_id]['message_id']
        offline_message_settings = self.db_offline[guild_id]['message_settings']

        embed = discord.Embed(title="", colour=discord.Colour.green())
        embed.add_field(name=offline_message_settings[ticket_reference]['name'],
                        value=offline_message_settings[ticket_reference]['value'])
        message = await channel_destination.send(embed=embed)
        await message.add_reaction(open_reaction_emoji)

        # GOING READY, UPDATE OFFLINE DATABASE
        offline_channel_id[ticket_reference] = channel_destination.id
        offline_message_id[ticket_reference] = message.id
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)

        await cursor.execute("UPDATE tickets_config SET channel_id = %s, message_id = %s WHERE server_id = %s;",
                             (str(offline_channel_id), str(offline_message_id), guild_id))
        await self.load_db_var(only_guild=guild_id)

    async def return_ticket_title_format(self, ticket_reference: str, ticket_number: int, name: str,
                                         ticket_title_mode):
        _ticket_title_mode = {ticket_reference: {'ticket_number': True,
                                                 'ticket_name': False,
                                                 'number_name': False,
                                                 'number_name_reference': False
                                                 }}

        for k, v in ticket_title_mode.items():
            if v is True:
                return await self.return_ticket_title_generated(ticket_number=ticket_number,
                                                                name=name,
                                                                reference=ticket_reference,
                                                                title_type=k)

    async def return_ticket_title_generated(self, ticket_number: int, name: str, reference: str, title_type: str):
        if title_type == 'ticket_number':
            return f"ticket-{ticket_number}"
        elif title_type == 'ticket_name':
            return f"ticket-{name}"
        elif title_type == 'number_name':
            return f"{ticket_number}-{name}"
        elif title_type == 'number_name_reference':
            return f"{ticket_number}-{name}-{translate_fronts(reference)}"

    async def create_ticket(self, guild_id: int, user_id: int, ticket_reference: str):
        # LOADING OFFLINE DATABASE
        ticket_general_category_id = self.db_offline[guild_id]['ticket_general_category_id'][ticket_reference]
        category = self.bot.get_channel(ticket_general_category_id)
        ticket_count = self.db_offline[guild_id]['ticket_count'][ticket_reference] + 1
        ticket_settings = self.db_offline[guild_id]['ticket_settings'][ticket_reference]
        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]
        ticket_reaction_lock_ids = self.db_offline[guild_id]['ticket_reaction_lock_ids'][ticket_reference]
        ticket_owner_id = self.db_offline[guild_id]['ticket_owner_id'][ticket_reference]
        ticket_title_mode = self.db_offline[guild_id]['ticket_title_mode'][ticket_reference]
        ticket_multiple = self.db_offline[guild_id]['ticket_multiple'][ticket_reference]

        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(user_id)
        # END
        # CHECK IF TICKET ALREADY EXIST
        if not ticket_multiple:
            if user_id in ticket_owner_id.values():
                # TRY TO MENTION USER IN HIS OWN TICKET
                try:
                    # ticket_owner_id[message.id] = user_id
                    oof = [k for k, v in self.db_offline[guild_id]['ticket_owner_id'][ticket_reference].items() if
                           v == user_id]
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

        ticket_title = await self.return_ticket_title_format(ticket_reference=ticket_reference,
                                                             ticket_number=ticket_count,
                                                             name=member.name,
                                                             ticket_title_mode=ticket_title_mode)
        overwrites = await self.return_overwrites(guild=guild,
                                                  member=member,
                                                  roles_ids=ticket_support_roles if ticket_support_roles else None,
                                                  everyone=False)

        channel = await guild.create_text_channel(ticket_title, overwrites=overwrites, category=category,
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
        await cursor.execute(f'UPDATE tickets_config SET ticket_count = %s, ticket_reaction_lock_ids = %s, '
                             f'ticket_owner_id = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_count']),
                              str(self.db_offline[guild_id]['ticket_reaction_lock_ids']),
                              str(self.db_offline[guild_id]['ticket_owner_id']),
                              guild.id), )

        await self.load_db_var(guild_id)
        disconn.close()

    async def add_support_role(self, guild_id: int, roles, ticket_reference: str):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)

        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]
        foo = ''
        updated_roles = []
        for role in roles:
            if role.id in ticket_support_roles:
                foo += f'⚠ ️Il ruolo {role.mention} ha già i permessi per geststire i ticket **{ticket_reference}** futuri\n'
            else:
                ticket_support_roles.append(role.id)
                updated_roles.append(role.id)
                foo += f'✅ Il ruolo {role.mention} ha i permessi per gestire i ticket  **{ticket_reference}** d\'ora in poi\n'

        await cursor.execute(f'UPDATE tickets_config SET ticket_support_roles = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_support_roles']), guild_id))
        await self.try_update_log_channel_overwrites(
            channel_log_id=self.db_offline[guild_id]['ticket_general_log_channel'][ticket_reference],
            roles_ids=updated_roles,
            add=True)
        await self.load_db_var(guild_id)
        return foo

    async def rem_support_role(self, guild_id: int, roles, ticket_reference: str):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)

        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles'][ticket_reference]
        foo = ''
        updated_roles = []
        for role in roles:
            if role.id in ticket_support_roles:
                ticket_support_roles.remove(role.id)
                updated_roles.append(role.id)
                foo += f'✅ Il ruolo {role.mention} non potrà gestire i ticket  **{ticket_reference}** d\'ora in poi'
            else:
                foo += f'⚠ ️Il ruolo {role.mention} non ha ancora  i permessi per gestire i ticket **{ticket_reference}**'

        await cursor.execute(f'UPDATE tickets_config SET ticket_support_roles = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_support_roles']), guild_id))
        await self.try_update_log_channel_overwrites(
            channel_log_id=self.db_offline[guild_id]['ticket_general_log_channel'][ticket_reference],
            roles_ids=updated_roles,
            add=False)
        await self.load_db_var(guild_id)
        return foo

    async def try_update_log_channel_overwrites(self, channel_log_id: int, roles_ids: list, add: bool = True):
        channel_log = self.bot.get_channel(channel_log_id)
        if channel_log:
            overwrites_old = channel_log.overwrites
            overwrites = await self.return_overwrites(guild=channel_log.guild,
                                                      roles_ids=roles_ids,
                                                      overwrites=overwrites_old,
                                                      everyone=False,
                                                      add=add if add else False)
            await channel_log.edit(overwrites=overwrites)

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

        if not channel:
            disconn = await aiomysql.connect(host=host,
                                             port=port,
                                             user=user,
                                             password=password,
                                             db=db,
                                             autocommit=True)

            cursor = await disconn.cursor(aiomysql.DictCursor)

            overwrites = await self.return_overwrites(guild=guild, everyone=False)
            channel = await guild.create_text_channel('🗂｜𝗔𝗥𝗖𝗛𝗜𝗩𝗜𝗢',
                                                      overwrites=overwrites,
                                                      category=category,
                                                      reason=None)
            offline_ticket_general_log_channel = self.db_offline[guild.id]['ticket_general_log_channel']

            offline_ticket_general_log_channel[ticket_reference] = channel.id
            await cursor.execute("UPDATE tickets_config SET ticket_general_log_channel = %s WHERE server_id = %s;",
                                 (str(offline_ticket_general_log_channel), guild.id))
            disconn.close()

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

        await cursor.execute(f'UPDATE tickets_config SET ticket_reaction_lock_ids = %s, '
                             f'ticket_owner_id = %s WHERE server_id = %s;',
                             (str(self.db_offline[guild_id]['ticket_reaction_lock_ids']),
                              str(self.db_offline[guild_id]['ticket_owner_id']), guild.id), )

        await self.load_db_var(guild_id)
        disconn.close()

    async def return_overwrites(self,
                                guild: discord.Guild,
                                overwrites: dict = None,
                                roles_ids: list = None,
                                member: discord.Member = None,
                                everyone: bool = True,
                                add: bool = True):

        # non ricordo a cosa revrica everyone true

        if not overwrites:
            overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=True if everyone else False,
                                                                          send_messages=False,
                                                                          add_reactions=False
                                                                          ), }

        if member:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True, )

        if roles_ids:
            for role in roles_ids:

                role_obj = guild.get_role(role)
                if role_obj:
                    if add:
                        overwrites[role_obj] = discord.PermissionOverwrite(read_messages=True, send_messages=True, )
                    else:
                        overwrites.pop(role_obj, None)
        return overwrites

    # TODO: ticket_closer_user_id DA RIMUOVERE
    # TODO: AGGIUNGERE COMANDO CLOSE
    # TODO: AGGIUNGERE CLAIM
    # TODO: AGGIUNGERE AMMINISTRATORE PUÒ CHIUDERE TICKET ANCHE NON IN SETUP
    # TODO: AGGIUNGERE OPEN TIME DEL TICKET
    # TODO: AGGIUNGERE REASON
    # TODO: PERMESSO REAZIONI DIVERSE DA QUELLE GIA ESISTENTI NEGATO
    # TODO: CREARE LOG MESSAGGI MANDATI QUANDO CHIUDO TICKET
    # TODO: POSSIBILITA DI RIAPRIRE I TICKET ENTRO 2 MINUTI DALLA CHISURA meh...
    # TODO: COMANDO ADD PER AGGIUNGERE UTENTE AL TICKET (*kwargs user) meh...
    # TODO: OPZIONALE  SE MANDI UN MESSAGGIO IN PRIVATO AL BOT APRE UN DM TICKET meh...
    # TODO: OPZIONALE SE HA IN COMUNE PIU DI UN SERVER DISCORD CHIEDE IN QUALE APRIRE IL TICKET meh...


def setup(bot):
    bot.add_cog(ticket(bot))
