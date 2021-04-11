import discord, urllib
from discord.ext import commands
from . import utils

class HeraldicStuff(commands.Cog, name="Heraldry"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		name="catalog",
		help="Looks up a term in DrawShield's repository of charges.\nCode © Karl"\
		" Wilcox",
		aliases=("charge","cat")
	)
	async def ds_catalog(self, ctx, *, charge):			
		url = find_in_catalog(charge)
		
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
		name="drawshield",
		help="Illustrates arms using DrawShield.\nNote that DrawShield does not support"\
		" all possible blazons. Code © Karl Wilcox",
		aliases=("ds",)
	)
	async def ds_draw(self, ctx, *, blazon : str):			
		embed = ds_backend(blazon,"Shield")
		await ctx.send(embed=embed)
		
	@commands.command(
		name="drawflag",
		help="Illustrates flags using DrawShield.\nNote that DrawShield does not support"\
		" all possible flags, and the vexillological functionality is still in early"\
		" development. Code © Karl Wilcox",
		aliases=("df",)
	)
	async def ds_drawflag(self, ctx, *, blazon : str):
		embed = ds_backend(blazon+" in flag shape","Flag")
		await ctx.send(embed=embed)
		
	@commands.command(
		name="lookup",
		help="Looks up heraldic terms using the DrawShield API.\nTerms are sourced from"\
		" Parker's and Elvin's heraldic dictionaries. Code © Karl Wilcox",
		aliases=("lu","define","def")
	)
	async def ds_lookup(self, ctx, *, term : str):
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
		
		thumb = find_in_catalog(term)
		if thumb: embed.set_thumbnail(url=thumb)
		
		await ctx.send(embed=embed)
		
def ds_backend(blazon,drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = utils.get_json(f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	
	embed = utils.nv_embed("",blazon,kind=4,custom_name=f"{drawn_kind} drawn!")		
	embed.set_image(url=f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=png&dummy=shield.png")
	embed.set_footer(text=f"Drawn using DrawShield; © Karl Wilcox. ")
	
	for message in results["messages"]:
		if message["category"] != "blazon": continue
		elif "linerange" in message:
			embed.add_field(name=f"Error {message['linerange']}",value=message["content"],inline=False)
		elif "context" in message:
			embed.add_field(name="Error",value=f"{message['content']} {message['context']}",inline=False)
			
	return embed
	
def find_in_catalog(charge):
	catalog = utils.get_json(f"https://drawshield.net/api/catalog/{urllib.parse.quote(charge)}")
	
	if not catalog.startswith("http"): return None
	return catalog

def setup(bot):
	bot.add_cog(HeraldicStuff(bot))