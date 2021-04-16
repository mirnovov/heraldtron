import discord, urllib, csv, json, random, re
from discord.ext import commands
from . import utils, services

class HeraldicStuff(commands.Cog, name="Heraldry"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help="Finds the first result of `coat of arms [query]` using Google Images.",
		aliases=("as",)
	)
	@commands.before_invoke(utils.typing)
	async def armssearch(self, ctx, *, query):
		embed = await services.gis("coat of arms " + query)
		await ctx.send(embed=embed)	
		
	@commands.command(
		name="catalog",
		help="Looks up a term in DrawShield's repository of charges.\nCode © Karl"\
		" Wilcox",
		aliases=("charge","cat")
	)
	@commands.before_invoke(utils.typing)
	async def ds_catalog(self, ctx, *, charge):			
		url = await services.ds_catalog(charge)
		
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
	@commands.before_invoke(utils.typing)
	async def ds_challenge(self, ctx, source="all"):			
		url = await utils.get_json(f"https://drawshield.net/api/challenge/{source}")
		
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
	@commands.before_invoke(utils.typing)
	async def drawshield(self, ctx, *, blazon : str):			
		embed = await services.ds(blazon,"Shield")
		await ctx.send(embed=embed)
		
	@commands.command(
		help="Looks up heraldic terms using the DrawShield API.\nTerms are sourced from"\
		" Parker's and Elvin's heraldic dictionaries. Code © Karl Wilcox",
		aliases=("lu","define","def")
	)
	@commands.before_invoke(utils.typing)
	async def lookup(self, ctx, *, term : str):
		results = await utils.get_json(f"https://drawshield.net/api/define/{urllib.parse.quote(term)}")
		
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
		
		thumb = await services.ds_catalog(term)
		if thumb: embed.set_thumbnail(url=thumb)
		
		await ctx.send(embed=embed)
		
	@commands.command(
		help="Generates a motto randomly.\n"\
		"The included functionality has several advancements over previous"\
		"motto generators.",
		aliases=("mt","mot")
	)
	@commands.before_invoke(utils.typing)
	async def motto(self, ctx):
		with open("data/mottoparts.json") as file:
			parts = json.load(file)
			
		percent = random.randrange(1,100)
		partlist = parts["templates"]["uni"] #1-20%
		
		if percent > 20 and percent < 51:
			partlist = parts["templates"]["nou"]
		elif percent > 50 and percent < 71:
			partlist = parts["templates"]["adj"]
		elif percent > 70:
			partlist = parts["templates"]["ver"]
			
		parts["uni_resolve"] = random.choice(["nou","adj"])
		parts["last_key"] = ""
				
		def chooseTerm(match):
			term_kind = match[0]
			
			if "uni" in term_kind:
				term_kind = term_kind[:1] + parts["uni_resolve"]
				
			term_list = parts["terms"][term_kind]
				
			if (parts["last_key"] != "1" and bool(random.getrandbits(1)) 
				and parts["last_key"] in term_list):
				#1 in 2 chance of choosing related terms for a non-initial item
				result = parts["last_key"]
			else:
				result = random.choice(list(term_list.keys()))
			
			parts["last_key"] = result
			return term_list.pop(result)
						
		template = random.choice(partlist)
		motto = re.sub("([&|!]\\w\\w\\w)",chooseTerm,template).capitalize()		
		
		await ctx.send(embed=utils.nv_embed(f"{motto}","",kind=4,custom_name="Motto generator"))
		
	@commands.command(
		help="Randomly selects a motto from a list of over 400.\n"\
		"These include countries, heads of state, and universities",
		aliases=("rmot","rm")
	)
	async def randmotto(self, ctx):
		with open("data/mottoes.csv") as file:
			row = random.choice(list(csv.reader(file, delimiter=";")))
					
		embed = utils.nv_embed(
			f"{row[1]}",
			f"**{row[0]}**",
			kind=3,
			custom_name="Random motto"
		)	
		
		if row[2].strip(" ") != "English":
			embed.description += f"\n*{row[3].strip(' ')}* ({row[2].strip(' ')})"	
					
		await ctx.send(embed=embed)
		
def setup(bot):
	bot.add_cog(HeraldicStuff(bot))