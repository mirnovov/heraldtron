import discord
from discord.ext import commands
from . import utils, services

class VexStuff(commands.Cog, name="Vexillology"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help="Searches Google Images for `flag <whatever you wrote>` and returns the first result.",
		aliases=("fs",)
	)
	async def flagsearch(self, ctx, *, query):
		embed = services.gis("flag " + query)
		await ctx.send(embed=embed)	
		
	@commands.command(
		help="Illustrates flags using DrawShield.\nNote that DrawShield does not support"\
		" all possible flags, and the vexillological functionality is still in early"\
		" development. Code © Karl Wilcox",
		aliases=("df",)
	)
	async def drawflag(self, ctx, *, blazon : str):
		embed = services.ds(blazon+" in flag shape","Flag")
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(VexStuff(bot))