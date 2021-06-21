import urllib, re
from discord.ext import commands
from .. import embeds, services, utils

class HeraldryReference(utils.MeldedCog, name = "Reference", category = "Heraldry"):
	SBW_SUB = re.compile(r"== *(.*) *==|'{2,4}([^']*)'{2,4}|<ref>.+?</ref>|<[^<]+?>|\[+[^\[]+?\]+")
	
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help = "Finds the results of `coat of arms [query]` using Google Images.",
		aliases = ("as",)
	)
	@utils.trigger_typing
	async def armssearch(self, ctx, *, query):
		await services.gis(ctx, "coat of arms " + query)
		
	@commands.command(
		help = "Looks up heraldic terms in the Finto HERO ontological database.",
		aliases = ("finto", "luh", "ontology", "he")
	)
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
		
	@commands.command(
		help = "Looks up heraldic terms using the DrawShield API.\nTerms are sourced from"
			   " Parker's and Elvin's heraldic dictionaries. Code © Karl Wilcox",
		aliases = ("lu", "define", "def")
	)
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
		if thumb: embed.set_thumbnail(url = thumb)
		
		await ctx.send(embed = embed)
		
	
		
	@commands.command(
		help = "Displays an entry from the Sourced Blazons Wiki.",
		aliases = ("w",)
	)
	@utils.trigger_typing
	async def sbw(self, ctx, *, query):
		title = urllib.parse.quote(query.title())
		response = await utils.get_json(
			self.bot.session,
			"https://sourcedblazons.fandom.com/api.php?action=query&titles="
			f"{title}&prop=revisions&rvslots=main&rvprop=content&rvlimit=1&format=json"
		)
		
		if response["query"]["pages"].get("-1"):
			raise utils.CustomCommandError(
				"Invalid page",
				f"The term could not be found. Check that it is entered correctly."
			)
			
		def wikitext_parse(matchobj):
			if matchobj.group(1) and "Sources" not in matchobj.group(1):
				return f"**{matchobj.group(1)}**"
			elif matchobj.group(2):
				return matchobj.group(2)
			else: return ""
		
		response = list(response["query"]["pages"].values())[0]
		text = re.sub(
			self.SBW_SUB,
			wikitext_parse,
			response["revisions"][0]["slots"]["main"]["*"]
		)
		
		if len(text) > 2048:
			text = f"{text[:2045]}..."
		
		embed = embeds.SEARCH_RESULT.create(response["title"], text, heading = "Sourced Blazons Wiki result")
		embed.url = f"https://sourcedblazons.fandom.com/wiki/{urllib.parse.quote(response['title'])}"
		
		await ctx.send(embed = embed)
		
	@commands.command(
		help = "Shows a list of commonly used tinctures.",
		aliases = ("t", "colours", "colors", "metals", "furs")
	)
	async def tinctures(self, ctx):
		await ctx.send(
			"In heraldry, *tinctures* are divided into:\n\n"
			"- **Colours**: :red_circle: Gules, :green_circle: Vert,"
			" :blue_circle: Azure, :black_circle: Sable, :purple_circle: Purpure\n\n"
			"- **Metals**: :yellow_circle: Or, :white_circle: Argent\n\n"
			"- **Furs**: Ermine, Vair, etc.\n\nThe *rule of tincture* states that colour"
			" cannot touch metal, except for minor details and field divisions; furs can touch both."
			"Keep in mind that the exact shades can vary. Various rarer tinctures also exist,"
			" but many dislike them; use with caution."
		)
	
def setup(bot):
	bot.add_cog(HeraldryReference(bot))