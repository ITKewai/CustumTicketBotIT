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
    print(f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot")
    await bot.change_presence(activity=discord.Game(name="BETA-DEVELOPING"))

bot.run('N'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'j'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'g'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '2'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'M'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'z'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'Q'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '0'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'N'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'j'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'g'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'y'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'M'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'T'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'U'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '4'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'M'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'j'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'k'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'z'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'M'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'D'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'g'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '5'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '.'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'X'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'm'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'V'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '2'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'S'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'w'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '.'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'f'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'Q'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'M'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'e'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '3'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'r'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'S'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'Q'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'B'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        '5'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'T'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'H'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'M'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'w'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'Q'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'h'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'z'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'y'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'Y'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'U'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'Z'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'V'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'o'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'x'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'd'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'A'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂
        'o'  # YES I KNOW THIS IS A BOT TOKEN BUT I DON'T CARE 😂)
        )
