# bot.py
import os, discord, logging
from discord.ext import commands
from dotenv import load_dotenv
from . import utils, help

logging.basicConfig(level=logging.INFO)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!")
bot.help_command = help.NvHelpCommand()
cogs = ["modtools","debug"]

@bot.event
async def on_ready():
	print(f"{bot.user} has connected to Discord!")
	
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
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
			"The command you entered must be formatted differently. Check that it is entered correctly and try again."
		))
	else:	
		raise error

if __name__ == "__main__":
	for cog in cogs:
		bot.load_extension(f"ht.{cog}")
		print(f"Cog {cog} loaded sucessfully")
	
	bot.run(TOKEN)