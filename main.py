import json
import discord
from discord.ext import commands
import os
import sys
import jishaku

intents = discord.Intents.default()
intents.members = True  # Subscribe to the privileged members intent.
intents.presences = True  # Subscribe to the privileged members intent.
intents.reactions = True
bot = commands.Bot(command_prefix='-', case_insensitive=True,
                   allowed_mentions=discord.AllowedMentions(everyone=False, roles=False), intents=intents)
bot.remove_command('help')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.load_extension('jishaku')


@bot.event
async def on_ready():
    print("Pronto come", bot.user)
    await bot.change_presence(activity=discord.Game(name="BETA-DEVELOPING"))

bot.run('Njg2MzQ0NjgyMTU4MjkzM'
        'Dg5.XmV2Sw.fQMe3rSQB5'
        'THMwQhzyYUZVoxdAo')
