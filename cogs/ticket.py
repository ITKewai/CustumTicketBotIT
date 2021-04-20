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
                    await self.create_ticket(self.bot, payload.guild_id)

    @commands.command()
    async def setup(self, ctx):
        await self.ready_db()
        await self.insert_ticket_db(guild=ctx.guild)

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
                                                        'ticket_reaction_lock_ids': y['ticket_reaction_lock_ids'],
                                                        'ticket_support_roles': y['ticket_support_roles'],
                                                        'ticket_owner_id': literal_eval(y['ticket_owner_id']) if y[
                                                            'ticket_owner_id'] else None,
                                                        'ticket_closer_user_id': y['ticket_closer_user_id']
                                                        }
        else:
            await cursor.execute('SELECT * FROM datacenter WHERE server_id = ;')
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
                                                        'ticket_reaction_lock_ids': y['ticket_reaction_lock_ids'],
                                                        'ticket_support_roles': y['ticket_support_roles'],
                                                        'ticket_owner_id': literal_eval(y['ticket_owner_id']) if y[
                                                            'ticket_owner_id'] else None,
                                                        'ticket_closer_user_id': y['ticket_closer_user_id']
                                                        }

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
                                 "ticket_settings text, ticket_reaction_lock_ids varchar(255), "
                                 "ticket_support_roles text, ticket_owner_id varchar(255), "
                                 "ticket_closer_user_id varchar(255));")
        await self.load_db_var()
        self.db_ready = True
        print(self.db_ready)

    async def create_ticket(self, bot, guild_id: int):
        guild = bot.get_guild(guild_id)

        ticket_general_category_id = self.db_offline[guild_id]['ticket_general_category_id']
        category = bot.get_channel(ticket_general_category_id)
        ticket_count = self.db_offline[guild_id]['ticket_count'] + 1
        ticket_settings = self.db_offline[guild_id]['ticket_settings']
        ticket_support_roles = self.db_offline[guild_id]['ticket_support_roles']

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False,)
        }
        if ticket_support_roles:
            for role in ticket_support_roles:
                role_obj = guild.get_role(role)
                if role_obj:
                    overwrites[role_obj] = discord.PermissionOverwrite(read_messages=True, send_messages=True,)

        channel = await guild.create_text_channel(f'ticket-{ticket_count}', overwrites=overwrites, category=category,
                                                  reason=None)
        embed = discord.Embed(title="", description=ticket_settings,
                              colour=discord.Colour.green())
        ticket_reaction_lock_ids = await channel.send(embed=embed)
        await ticket_reaction_lock_ids.add_reaction('🔒')

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
                                 "ticket_general_log_channel, ticket_count, ticket_settings) "
                                 "VALUES (%s, %s, %s, %s, %s, %s, %s,"
                                 " %s, %s);", (guild.id, category.id, channel.id, message.id,
                                               '📩', str(ticket_set), channel_archive.id, 0,
                                               ticket_settings))
            await self.load_db_var()
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


def setup(bot):
    bot.add_cog(Ticket(bot))
