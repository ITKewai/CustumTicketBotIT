import inspect
import json
import os
import io
import textwrap
import traceback
from contextlib import redirect_stdout
import aiohttp
import asyncio
import discord
from discord.ext import commands


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')


class DM(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @commands.command(aliases=['eval'], description='SUDO', pass_context=True, hidden=True)
    @commands.is_owner()
    async def test(self, ctx, *, body: str = None):
        if body:
            if ctx.author.id == 323058900771536898:
                env = {

                    'bot': self.bot,
                    'self': self,
                    'ctx': ctx,
                    'channel': ctx.channel,
                    'author': ctx.author,
                    'guild': ctx.guild,
                    'message': ctx.message,
                    '_': self._last_result
                }

                env.update(globals())

                body = cleanup_code(body)
                stdout = io.StringIO()

                to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

                try:
                    exec(to_compile, env)
                except Exception as e:
                    return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

                func = env['func']
                try:
                    with redirect_stdout(stdout):
                        ret = await func()
                except Exception as e:
                    value = stdout.getvalue()
                    await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
                else:
                    value = stdout.getvalue()
                    try:
                        await ctx.message.add_reaction('\u2705')
                    except:
                        pass

                    if ret is None:
                        if value:
                            await ctx.send(f'```py\n{value}\n```')
                    else:
                        self._last_result = ret
                        await ctx.send(f'```py\n{value}{ret}\n```')
        else:
            await ctx.send('Cosa devo testare?')



def setup(bot):
    bot.add_cog(DM(bot))