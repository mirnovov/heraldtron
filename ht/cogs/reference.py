import discord, urllib, re
from discord import app_commands
from discord.ext import commands
from .. import embeds, services, utils

class HeraldryReference(utils.MeldedCog, name = "Reference", category = "Heraldry"):
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
		help = "Looks up heraldic terms in the Finto HERO ontological database.",
		aliases = ("finto", "luh", "ontology", "he")
	)
	@app_commands.describe(term = "The heraldic term to look up.")
	@utils.trigger_typing
	async def hero(self, ctx, *, term):
		query = await utils.get_json(
			self.bot.session,
			f"http://api.finto.fi/rest/v1/search?vocab=hero&query={urllib.parse.quote(term)}&lang=en"
		)

		if len(query["results"]) == 0:
			raise utils.CustomCommandError(
				"Invalid HERO term",
				"The term could not be found. Check that it is entered correctly, or try other sources."
			)

		uri = query["results"][0]["uri"]

		results = await utils.get_json(
			self.bot.session,
			f"http://api.finto.fi/rest/v1/hero/data?format=application%2Fjson&uri={urllib.parse.quote(uri)}&lang=en"
		)
		results = results["graph"]
		embed = embeds.SEARCH_RESULT.create(f"Results for \"{term}\"", f"", heading = "HERO results")

		for result in results:
			if result["uri"] == "http://www.yso.fi/onto/hero/": continue
			elif result["uri"] == uri: result_type = "**Primary**:"
			elif result.get("narrower"): result_type = "Broader:"
			elif result.get("broader"): result_type = "Narrower:"
			else: result_type = "Related:"

			result_name = "(unknown)"

			if result.get("prefLabel"):
				for lang_label in result.get("prefLabel"):
					if lang_label["lang"] != "en": continue
					result_name = lang_label["value"]
					break

			en_uri = result["uri"].replace("http://www.yso.fi/onto/hero/","http://finto.fi/hero/en/page/")
			embed.description += f"- {result_type} [{result_name}]({en_uri})\n"

		embed.set_footer(text = f"Term retrieved using Finto HERO.")
		await ctx.send(embed = embed)

	@commands.hybrid_command(
		help = "Looks up heraldic terms using Parker's and Elvin's heraldic dictionaries. \nThis uses"
			   "the DrawShield API. Code © Karl Wilcox",
		aliases = ("lu", "define", "def")
	)
	@app_commands.describe(term = "The heraldic term to look up.")
	@utils.trigger_typing
	async def lookup(self, ctx, *, term : str):
		results = await utils.get_json(self.bot.session, f"https://drawshield.net/api/define/{urllib.parse.quote(term)}")

		if "error" in results:
			raise utils.CustomCommandError(
				"Invalid DrawShield term",
				"The term could not be found. Check that it is entered correctly, or try other sources."
			)

		embed = embeds.SEARCH_RESULT.create(
			f"Results for \"{term}\"",
			f"{results['content']}\n\u200b\n[View original entry]({results['URL']})",
		)
		embed.set_footer(text=f"Term retrieved using DrawShield; © Karl Wilcox. ")

		thumb = await services.ds_catalog(self.bot.session, term)
		if thumb: embed.set_thumbnail(url = thumb[0])

		await ctx.send(embed = embed)

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
