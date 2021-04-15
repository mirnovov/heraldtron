import discord
from discord.ext import commands
from . import utils

class DebugTools(commands.Cog, name="Debug", command_attrs=dict(hidden=True)):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(
		name="exit",
		help="Terminates the bot, for debugging and maintenance purposes.",
		aliases=("terminate","quit","kill","murder","x")
	)
	@utils.is_admin()
	async def terminate(self,ctx):
		await ctx.send(f"Terminating **{self.bot.user.mention}**...")
		await self.bot.close()
		
	@commands.command(name="reload",help="Reloads all extensions.",aliases=("rr",))
	@utils.is_admin()
	async def reload_cogs(self,ctx):
		extensions = [cog for cog in self.bot.extensions]
		for cog in extensions:
			self.bot.reload_extension(cog)
		print("Extensions reloaded!")
	
	@commands.command(name="error",help="Creates an error.",aliases=("err",))
	@utils.is_admin()
	async def raise_error(self,ctx):
		raise commands.CommandError("Test Error")
		
def setup(bot):
	bot.add_cog(DebugTools(bot))