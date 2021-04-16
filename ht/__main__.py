# bot.py
import os, discord, logging, traceback, sys
from discord.ext import commands
from dotenv import load_dotenv
from . import utils, help

logging.basicConfig(level=logging.INFO)
load_dotenv()

bot = commands.Bot(command_prefix="!",help_command=help.NvHelpCommand())
cogs = ["modtools","debug","heraldry","vexillology"]

@bot.event
async def on_ready():
	print(f"{bot.user} has connected to Discord!")
	
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		phrase = ctx.message.content
		
		if(phrase.startswith("!!") or phrase.startswith("!?")):
			return #ignore "!!!" etc
		
		await ctx.send(embed=utils.nv_embed(
			"Command not found",
			"The command you entered does not exist. Check your spelling and try again."
		))
	elif isinstance(error, commands.NoPrivateMessage):
		await ctx.send(embed=utils.nv_embed(
			"Command must be public",
			"The command you entered cannot be used during direct messaging."
		))
	elif isinstance(error, commands.MissingRole):
		await ctx.send(embed=utils.nv_embed(
			"Command requires elevated privileges",
			"The command you entered requires a role that you do not possess."
		))
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(embed=utils.nv_embed(
			"Command formatted incorrectly",
			f"The command you entered must be formatted differently. Check that it is entered correctly and try again."
		))
	else:
		cause = error if not isinstance(error, commands.CommandInvokeError) else error.original
		trace = "".join(traceback.format_tb(cause.__traceback__))
		maintainer = await bot.fetch_user(668627671306993703)
		dm = await maintainer.create_dm()	
		
		await ctx.send(embed=utils.nv_embed(
			"Unknown error",
			f"Heraldtron has encountered an unforseen difficulty. An error report has been sent."
		))
		await dm.send(embed=utils.nv_embed(
			"Unknown error",
			f"Heraldtron has encountered an unforseen difficulty due to a [command]({ctx.message.jump_url}).\n\n"\
			f"**Error Info**:\n```python\n{type(cause).__name__}: {str(cause)}\n```\n"
			f"**Stack Trace**:\n```python\n{trace}\n```"
		))

if __name__ == "__main__":
	for cog in cogs:
		bot.load_extension(f"ht.{cog}")
		print(f"Cog {cog} loaded sucessfully")
	
	bot.run(os.environ["DISCORD_TOKEN"])