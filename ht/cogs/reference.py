import discord, re, urllib
from discord import app_commands
from discord.ext import commands
from .. import embeds, services, utils

class HeraldryReference(utils.MeldedCog, name = "Reference", category = "Heraldry"):
	DS_URL = re.compile(r"https://drawshield\.net/reference/(.*)/./(.*)\.html")
	SBW_SUB = re.compile(r"={2,3}(.*?)={2,3}|'{2,4}([^']*)'{2,4}|<ref>.+?</ref>|<[^<]+?>|!?\[+([^\[]+?)\]+|(\n#)")
	SBW_LINK_NS = ("Category", "File")

	def __init__(self, bot):
		self.bot = bot

	@commands.hybrid_command(
		name = "as",
		help = "Finds the results of `coat of arms [query]` using Google Images.",
		aliases = ("armssearch",)
	)
	@app_commands.describe(query = "The search query to use.")
	@utils.trigger_typing
	async def armssearch(self, ctx, *, query):
		await services.gis(ctx, "coat of arms " + query)

	@commands.hybrid_command(
		help = "Looks up terms in Finto HERO and Parker's or Elvin's heraldic dictionaries.",
		aliases = ("finto", "hero", "luh", "ontology", "he", "lu", "define", "def")
	)
	@app_commands.describe(term = "The heraldic term to look up.")
	@utils.trigger_typing
	async def lookup(self, ctx, *, term):
		embed = embeds.SEARCH_RESULT.create("", "", heading = "Search results")
		embed.set_footer(text = f"Term retrieved using Finto HERO and DrawShield; the latter © Karl Wilcox ")

		hero_desc, hero_image = await services.hero(self.bot.session, term)
		
		if hero_desc:
			embed.description += hero_desc
		
		if hero_image:
			embed.set_thumbnail(url = f"attachment://{hero_image.filename}")
		
		ds_term = urllib.parse.quote(term.replace(" ", ""))
		ds_results = await utils.get_json(self.bot.session, f"https://drawshield.net/api/define/{ds_term}")

		if "error" not in ds_results:
			match = self.DS_URL.fullmatch(ds_results["URL"])
			embed.description += (
				f"### {match[1].capitalize()}'s dictionary result\n"
				f"[**{match[2]}**]({ds_results['URL']})\n" +
				ds_results["content"]
			)
		
		if embed.description == "":
			raise utils.CustomCommandError(
				"Invalid lookup term",
				"The term could not be found in Finto HERO, Parker's dictionary, or Elvin's dictionary. " 
				"Check that it is entered correctly, or try other sources."
			)

		await ctx.send(embed = embed, file = hero_image)

	@commands.hybrid_command(
		help = "Displays an entry from the Sourced Blazons Wiki.",
		aliases = ("w",)
	)
	@app_commands.describe(query = "The country, subdivision, or municipality to look up.")
	@utils.trigger_typing
	async def sbw(self, ctx, *, query):
		title = urllib.parse.quote(query.title())
		response = await utils.get_json(
			self.bot.session,
			"https://sourcedblazons.miraheze.org/w/api.php?action=query&titles="
			f"{title}&prop=revisions&rvslots=main&rvprop=content&rvlimit=1&format=json"
		)

		if response["query"]["pages"].get("-1"):
			raise utils.CustomCommandError(
				"Invalid page",
				f"The term could not be found. Check that it is entered correctly."
			)

		response = list(response["query"]["pages"].values())[0]
		text = re.sub(
			self.SBW_SUB,
			self.wikitext_parse,
			response["revisions"][0]["slots"]["main"]["*"]
		)

		if len(text) > 2048:
			text = f"{text[:2045]}..."

		embed = embeds.SEARCH_RESULT.create(response["title"], text, heading = "Sourced Blazons Wiki result")
		embed.url = f"https://sourcedblazons.miraheze.org/wiki/{urllib.parse.quote(response['title'])}"

		await ctx.send(embed = embed)

	@commands.hybrid_command(
		help = "Shows a short blurb about using supporters.",
		aliases = ("supporter",)
	)
	async def supporters(self, ctx):
		with open("media/prose/supporters.md", "r") as file:
			await ctx.send(file.read())

	@commands.hybrid_command(
		help = "Shows a short blurb about charges.",
	)
	async def charges(self, ctx):
		with open("media/prose/charges.md", "r") as file:
			await ctx.send(file.read())

	@commands.hybrid_command(
		help = "Shows a list of commonly used tinctures.",
		aliases = ("t", "colours", "colors", "metals", "furs", "tincture")
	)
	async def tinctures(self, ctx):
		with open("media/prose/tinctures.md", "r") as file:
			await ctx.send(file.read())
		
	@commands.hybrid_command(
		help = "Shows a short blurb about 'family crests'.",
		aliases = ("f", "familycrests", "crest", "crests", "inheritance", "bucket")
	)
	async def familycrest(self, ctx):
		with open("media/prose/familycrests.md", "r") as file:
			await ctx.send(file.read())
			
	@commands.hybrid_command(
		help = "Shows a short blurb about fridge testing.",
		aliases = ("fr", "fridgetest", "fridgetesting")
	)
	async def fridge(self, ctx):
		with open("media/prose/fridgetesting.md", "r") as file:
			await ctx.send(file.read())
			
	@commands.hybrid_command(
		help = "Shows a short blurb about false quartering.",
		aliases = ("fq",)
	)
	async def falsequartering(self, ctx):
		with open("media/prose/falsequartering.md", "r") as file:
			await ctx.send(file.read())
	
	def wikitext_parse(self, matchobj):
		if matchobj.group(1): #headings
			return f"**{matchobj.group(1).strip()}**"
		
		elif matchobj.group(2): #bold/italics
			return matchobj.group(2)
		
		elif matchobj.group(3): #links
			if (
				matchobj.group(3).split(":")[0] in self.SBW_LINK_NS or 
				matchobj.group(0).startswith("!")
			):
				return " "
			elif " " not in matchobj.group(3):
				return matchobj.group(3)
			else:
				url, name = matchobj.group(3).split(" ", 1)
				return f"[{name}]({url})"
		
		elif matchobj.group(4): #numbered lists
			return "\n1."
		
		else: return ""

async def setup(bot):
	await bot.add_cog(HeraldryReference(bot))
