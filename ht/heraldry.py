import discord
from discord.ext import commands
from . import utils, services

class HeraldicStuff(commands.Cog, name="Heraldry"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help="Searches Google Images for `coat of arms <whatever you wrote>` and returns the first result.",
		aliases=("as",)
	)
	async def armssearch(self, ctx, *, query):
		embed = services.gis("coat of arms " + query)
		await ctx.send(embed=embed)	
		
	@commands.command(
		name="catalog",
		help="Looks up a term in DrawShield's repository of charges.\nCode © Karl"\
		" Wilcox",
		aliases=("charge","cat")
	)
	async def ds_catalog(self, ctx, *, charge):			
		url = services.ds_catalog(charge)
		
		if url == None:
			await ctx.send(embed=utils.nv_embed(
				"Invalid catalog item",
				"Check your spelling and try again."
			))
			return
		
		embed = utils.nv_embed(
			f"Catalog entry for \"{charge}\"",
			"",
			kind=3,
			custom_name="DrawShield catalog"
		)		
		embed.set_image(url=url)
		embed.set_footer(text=f"Retrieved using DrawShield; © Karl Wilcox. ")
		
		await ctx.send(embed=embed)
		
	@commands.command(
		name="challenge",
		help="Displays a random image using the DrawShield API.\nDesigned to serve as an"\
		" emblazonment challenge using DrawShield. Code © Karl Wilcox; images © coadb,"\
		" The Book of Public Arms, Wikimedia Commons contributors (individual sources"\
		" can be selected via *coadb*, *public*, and *wikimedia* respectively).",
		aliases=("random","cl")
	)
	async def ds_challenge(self, ctx, source="all"):			
		url = utils.get_json(f"https://drawshield.net/api/challenge/{source}")
		
		if isinstance(url, dict) and "error" in url:
			await ctx.send(embed=utils.nv_embed(
				"Invalid challenge category",
				"Type !help challenge to see the available categories."
			))
			return
		
		embed = utils.nv_embed("","Try emblazoning this using DrawShield!",kind=4,custom_name="Random Image")		
		embed.set_image(url=url)
		embed.set_footer(text=f"Retrieved using DrawShield; © Karl Wilcox. ")
		
		await ctx.send(embed=embed)
		
	@commands.command(
		help="Illustrates arms using DrawShield.\nNote that DrawShield does not support"\
		" all possible blazons. Code © Karl Wilcox",
		aliases=("ds",)
	)
	async def drawshield(self, ctx, *, blazon : str):			
		embed = services.ds(blazon,"Shield")
		await ctx.send(embed=embed)
		
	@commands.command(
		help="Looks up heraldic terms using the DrawShield API.\nTerms are sourced from"\
		" Parker's and Elvin's heraldic dictionaries. Code © Karl Wilcox",
		aliases=("lu","define","def")
	)
	async def lookup(self, ctx, *, term : str):
		results = utils.get_json(f"https://drawshield.net/api/define/{urllib.parse.quote(term)}")
		
		if "error" in results:
			await ctx.send(embed=utils.nv_embed(
				"Invalid DrawShield term",
				"The term could not be found. Check that it is entered correctly, or try other sources."
			))
			return
		
		embed = utils.nv_embed(
			f"Results for \"{term}\"",
			f"{results['content']}\n\u200b\n[View original entry]({results['URL']})",
			kind=3
		)
		embed.set_footer(text=f"Term retrieved using DrawShield; © Karl Wilcox. ")
		
		thumb = services.ds_catalog(term)
		if thumb: embed.set_thumbnail(url=thumb)
		
		await ctx.send(embed=embed)
		
def setup(bot):
	bot.add_cog(HeraldicStuff(bot))