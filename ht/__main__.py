# bot.py
import os, discord, logging, traceback, sys
from discord.ext import commands
from dotenv import load_dotenv
from . import utils

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(
	command_prefix="!",
	description="A heraldry-related bot designed for the Heraldry Community.",
	activity=discord.Game("a !challenge")
)
bot.conf = utils.load_conf()
	
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		phrase = ctx.message.content
		
		if(phrase.startswith("!!") or phrase.startswith("!?")):
			return #ignore "!!!" etc
		
		title = "Command not found"
		message = "The command you entered does not exist. Check your spelling and try again."
		
	elif isinstance(error, commands.NoPrivateMessage):
		title = "Command must be public"
		message = "The command you entered cannot be used during direct messaging."
		
	elif isinstance(error, commands.MissingRole):
		title = "Command requires elevated privileges"
		message = "The command you entered requires a role that you do not possess."
		
	elif isinstance(error, commands.MissingRequiredArgument):
		title = "Command is missing argument"
		message = f"The command you entered requires the *{error.param.name}* argument."\
				  " Check that it is entered correctly and try again."
		
	elif isinstance(error, commands.UserNotFound):
		title = "Command could not locate user",
		message = f"The command you entered requires a valid user."\
				  " Check that their name is mentioned correctly and try again."
		
	#elif isinstance(error, commands.TooManyArguments):
	#	title = "Command given too many arguments",
	#	message = f"The command you entered does not accept this many arguments."\
	#			  " Check that you are using it correctly and try again."
	#	
	else:
		cause = error if not isinstance(error, commands.CommandInvokeError) else error.original
		trace = "".join(traceback.format_tb(cause.__traceback__))
		app_info = await bot.application_info()
		dm = await app_info.owner.create_dm()	
		
		if not isinstance(ctx.channel, discord.abc.GuildChannel) and not bot.is_owner(ctx.author):
			title = "Unknown error"
			message = f"Heraldtron has encountered an unforseen difficulty. An error report has been sent."
		
		await dm.send(embed=utils.nv_embed(
			"Unknown error",
			f"Heraldtron has encountered an unforseen difficulty due to a [command]({ctx.message.jump_url}).\n\n"\
			f"**Error Info**:\n```python\n{type(cause).__name__}: {str(cause)}\n```\n"
			f"**Stack Trace**:\n```python\n{trace}\n```"
		))
	
	await ctx.send(embed=utils.nv_embed(title,message))

if __name__ == "__main__":
	cogs = ["modtools","heraldry","misc","vexillology","meta"]
	
	for cog in cogs:
		bot.load_extension(f"ht.cogs.{cog}")
		print(f"Cog {cog} loaded sucessfully")
		
	if bot.conf.get("USE_JISHAKU"):
		os.environ["JISHAKU_HIDE"] = "1" 
		bot.load_extension("jishaku")
	
	bot.run(bot.conf["DISCORD_TOKEN"])