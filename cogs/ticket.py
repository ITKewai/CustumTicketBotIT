import asyncio
import json
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
        print(self.db_ready)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.first_scan_db()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id in self.db_offline:
            if payload.message_id == self.db_offline[payload.guild_id]['message_id']:
                if str(payload.emoji) == self.db_offline[payload.guild_id]['open_reaction_emoji']:
                    # channel = self.bot.get_channel(payload.channel_id)
                    # guild = self.bot.get_guild(payload.guild_id)
                    # member = guild.get_member(payload.user_id)
                    # message = await channel.fetch_message(payload.message_id)
                    # await message.remove_reaction(str(payload.emoji), member)
                    await self.create_ticket(payload.guild_id, payload.user_id)

    @commands.command()
    async def setup(self, ctx):
        await self.ready_db()
        await self.insert_ticket_db(guild=ctx.guild)

    @commands.command()
    async def delete(self, ctx):
        for channel in ctx.guild.channels:
            await channel.delete()

    @commands.command(aliases=['pan'], description='SUDO', pass_context=True, hidden=True)
    async def create_reaction_panel(self, ctx):
        embed = discord.Embed(title="Apri un Ticket!", description='Clicca la letterina della posta 📩 sotto',
                              colour=discord.Colour.green())
        await ctx.send(embed=embed)

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

    # FUNZIONI DATABASE
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
                self.db_offline[int(y['server_id'])] = {'ticket_general_category_id': y['ticket_general_category_id'],
                                                        'channel_id': y['channel_id'],
                                                        'message_id': y['message_id'],
                                                        'open_reaction_emoji': y['open_reaction_emoji'],
                                                        'message_settings': literal_eval(y['message_settings']),
                                                        'ticket_general_log_channel': y['ticket_general_log_channel'],
                                                        'ticket_count': y['ticket_count'],
                                                        'ticket_settings': y['ticket_settings'],
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
            self.db_offline[int(y['server_id'])] = {'ticket_general_category_id': y['ticket_general_category_id'],
                                                    'channel_id': y['channel_id'],
                                                    'message_id': y['message_id'],
                                                    'open_reaction_emoji': y['open_reaction_emoji'],
                                                    'message_settings': literal_eval(y['message_settings']),
                                                    'ticket_general_log_channel': y['ticket_general_log_channel'],
                                                    'ticket_count': y['ticket_count'],
                                                    'ticket_settings': y['ticket_settings'],
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
                                 "ticket_general_category_id bigint(20), channel_id bigint(20), "
                                 "message_id bigint(20), open_reaction_emoji varchar(255), message_settings text, "
                                 "ticket_general_log_channel bigint(20), ticket_count bigint(20), "
                                 "ticket_settings text, ticket_reaction_lock_ids text, "
                                 "ticket_support_roles text, ticket_owner_id text, "
                                 "ticket_closer_user_id varchar(255));")
        await self.load_db_var()
        self.db_ready = True
        disconn.close()
        print(self.db_ready)

    async def create_ticket(self, guild_id: int, user_id: int):
        # LOADING OFFLINE DATABASE
        ticket_general_category_id = self.db_offline[guild_id]['ticket_general_category_id']
        category = self.bot.get_channel(ticket_general_category_id)
        ticket_count = self.db_offline[guild_id]['ticket_count'] + 1
        ticket_settings = self.db_offline[guild_id]['ticket_settings']
        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles']
        ticket_reaction_lock_ids = self.db_offline[guild_id]['ticket_reaction_lock_ids']
        ticket_owner_id = self.db_offline[guild_id]['ticket_owner_id']
        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(user_id)
        # END
        # CHECK IF TICKET ALREADY EXIST
        if user_id in ticket_owner_id.values():
            return await member.send('Hai già un ticket aperto ! ')
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
        message = await channel.send(embed=embed)
        # END

        # UPDATE DATABASE DATA
        ticket_reaction_lock_ids[message.id] = channel.id
        ticket_owner_id[message.id] = user_id

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
                             (ticket_count, str(ticket_reaction_lock_ids), str(ticket_owner_id), guild.id), )

        await self.load_db_var(guild_id)
        disconn.close()

    async def ready_db(self):
        await self.bot.wait_until_ready()
        while not self.db_ready:
            await asyncio.sleep(1)
        return True

    async def insert_ticket_db(self, guild):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)

        category = await guild.create_category('TICKET', overwrites=None, reason='Ticket bot', position=0)
        channel = await guild.create_text_channel('🔖｜𝗧𝗜𝗖𝗞𝗘𝗧', overwrites=None, category=category, reason=None)
        channel_archive = await guild.create_text_channel('🗂｜𝗔𝗥𝗖𝗛𝗜𝗩𝗜𝗢', overwrites=None, category=category,
                                                          reason=None)
        # 𝗔𝗕𝗖𝗗 sans serif Grasso - https://www.topster.it/testo/utf-schriften.html
        embed = discord.Embed(title="", colour=discord.Colour.green())
        ticket_set = {'name': 'Apri un Ticket!', 'value': 'Clicca la letterina della posta 📩 sotto '}
        embed.add_field(name=ticket_set['name'], value=ticket_set['value'])
        message = await channel.send(embed=embed)
        emoji = '📩'
        await message.add_reaction(emoji)

        ticket_settings = 'Il supporto sarà con te a breve.\n Per chiudere questo ticket reagisci con 🔒 sotto'

        try:
            await cursor.execute("INSERT INTO datacenter (server_id, ticket_general_category_id, "
                                 "channel_id, message_id, open_reaction_emoji, message_settings, "
                                 "ticket_general_log_channel, ticket_count, ticket_settings, ticket_reaction_lock_ids, "
                                 "ticket_support_roles, ticket_owner_id, ticket_closer_user_id) "
                                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
                                 " %s, %s);", (guild.id, category.id, channel.id, message.id,
                                               '📩', str(ticket_set), channel_archive.id, 0,
                                               ticket_settings, str({}), str([]), str({}), str({})))
            await self.load_db_var(only_guild=guild.id)
        except Exception as error:
            print(error)

        disconn.close()

    async def add_support_role_ticket_db(self, bot, guild, role_ids: list):
        disconn = await aiomysql.connect(host=host,
                                         port=port,
                                         user=user,
                                         password=password,
                                         db=db,
                                         autocommit=True)
        cursor = await disconn.cursor(aiomysql.DictCursor)
        await cursor.execute(f"UPDATE x{guild.id} SET WHERE 1;")

    async def remove_support_role_ticket_db(self):
        pass

    async def close_ticket(self):
        pass

def setup(bot):
    bot.add_cog(Ticket(bot))
