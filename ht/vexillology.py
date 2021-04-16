import discord
from discord.ext import commands
from . import utils, services

class VexStuff(commands.Cog, name="Vexillology"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help="Finds the first result of `flag [query]` using Google Images.",
		aliases=("fs",)
	)
	@commands.before_invoke(utils.typing)
	async def flagsearch(self, ctx, *, query):
		embed = await services.gis("flag " + query)
		await ctx.send(embed=embed)	
		
	@commands.command(
		help="Illustrates flags using DrawShield.\nNote that DrawShield does not support"\
		" all possible flags, and the vexillological functionality is still in early"\
		" development. Code © Karl Wilcox",
		aliases=("df",)
	)
	@commands.before_invoke(utils.typing)
	async def drawflag(self, ctx, *, blazon : str):
		embed = await services.ds(blazon+" in flag shape","Flag")
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(VexStuff(bot))