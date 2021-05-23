import discord, asyncio, typing, urllib, csv, json, random, re
from discord.ext import commands
from .. import converters, embeds, services, utils
from ..artifacts import Source

class HeraldicStuff(commands.Cog, name = "Heraldry"):
	MOTTO_PARTS = re.compile("([&|!]\\w\\w\\w)")
	RESOURCE = re.compile("(?s)<li.*?data-key=\"(.+?)\">.*?<a href=\"(.+?)\">(.+?)</a>.*?<p>(.+?)</p>")
	RES_SUB_A = re.compile("<i>|</i>")
	RES_SUB_B = re.compile("<[^<]+?>")
	
	def __init__(self, bot):
		self.bot = bot
		
	async def cog_check(self, ctx):
		return await utils.check_limited(ctx)
		
	@commands.command(
		help = "Displays a random historical heraldic artifact.\n"\
			"This can be narrowed down to an individual source:\n\n"\
			f"{Source.str_list()}",
		aliases = ("ar", "relic")
	)
	@utils.trigger_typing
	async def artifact(self, ctx, source = "all"):
		if source == "all":
			museum = Source.random()
		elif source in Source.register:
			museum = Source.register[source]
		else:
			raise utils.CustomCommandError(
				"Invalid artifact source",
				"Check your spelling and try again."
			)
			
		result = await museum.retrieve(ctx.bot)
		embed = embeds.SEARCH_RESULT.create(result[1], result[2], heading = "Random artifact")
		embed.url = result[0]	
		embed.set_footer(text = f"{result[4]} via {museum.desc}" if result[4] else museum.desc)
		
		if result[3]: embed.set_image(url = result[3])
		
		await ctx.send(embed = embed)	
		
	@commands.command(
		help = "Looks up an user's coat of arms.\nUses GreiiEquites' Book of Arms as a source."\
			   "If `alternate_emblazon` is enabled, also shows a user-selected emblazon, like with `!emblazon`."\
			   "This is off by default as Greii eventually aims to implement a consistent emblazon style",
		aliases = ("a", "greiin", "showarms", "arms")
	)
	@utils.trigger_typing
	async def armiger(self, ctx, alt_emblazon: typing.Optional[converters.ImageTag] = False, user: converters.Armiger = None):
		if not user:
			user = await utils.fetchone(
				ctx.bot.dbc, "SELECT * FROM armigers_e WHERE discord_id == ?;", (ctx.author.id,)
			)
		
		embed = embeds.GENERIC.create(f"{user[2]}#{user[3]}", user[4], heading = f"GreiiN:{user[0]:04}")
		embed.set_footer(text = "From the Book of Arms by GreiiEquites")
		
		if user[6] and alt_emblazon:
			embed.set_thumbnail(url = user[6])
		
		await ctx.send(embed = embed)
			
	@commands.command(
		help = "Finds the results of `coat of arms [query]` using Google Images.",
		aliases = ("as",)
	)
	@utils.trigger_typing
	async def armssearch(self, ctx, *, query):
		await services.gis(ctx, "coat of arms " + query)
		
	@commands.command(
		name = "catalog",
		help = "Looks up a term in DrawShield's repository of charges.\nCode © Karl Wilcox",
		aliases = ("charge", "cat")
	)
	@utils.trigger_typing
	async def ds_catalog(self, ctx, *, charge):			
		url = await services.ds_catalog(self.bot.session, charge)
		
		if url == None: raise utils.CustomCommandError(
			"Invalid catalog item",
			"Check your spelling and try again."
		)
		
		embed = embeds.SEARCH_RESULT.create(
			f"Catalog entry for \"{charge}\"", "",
			heading = "DrawShield catalog"
		)		
		embed.set_image(url=url)
		embed.set_footer(text=f"Retrieved using DrawShield; © Karl Wilcox. ")
		
		await ctx.send(embed=embed)
		
	@commands.command(
		name = "challenge",
		help = "Displays a random image using the DrawShield API.\nDesigned to serve as an"\
		" emblazonment challenge using DrawShield. Code © Karl Wilcox; images © coadb,"\
		" The Book of Public Arms, Wikimedia Commons contributors (individual sources"\
		" can be selected via *coadb*, *public*, and *wikimedia* respectively).",
		aliases=("random","cl")
	)
	@utils.trigger_typing
	async def ds_challenge(self, ctx, source="all"):			
		url = await utils.get_json(self.bot.session, f"https://drawshield.net/api/challenge/{source}")
		
		if isinstance(url, dict) and "error" in url:
			raise utils.CustomCommandError(
				"Invalid challenge category",
				"Type `!help challenge` to see the available categories."
			)
		
		embed = embeds.GENERIC.create("","Try emblazoning this using DrawShield!", heading = "Random image")		
		embed.set_image(url = url)
		embed.set_footer(text = "Retrieved using DrawShield; © Karl Wilcox. ")
		
		await ctx.send(embed = embed)
		
	@commands.command(
		help = "Illustrates arms using DrawShield.\nNote that DrawShield does not support"\
		" all possible blazons. Code © Karl Wilcox",
		aliases = ("ds",)
	)
	@utils.trigger_typing
	async def drawshield(self, ctx, *, blazon : str):			
		embed, file = await services.ds(self.bot.session, blazon, "Shield")
		await ctx.send(embed = embed, file = file)
		
	@commands.command(
		help = "Looks up a user-defined emblazon of a coat of arms.",
		aliases = ("e",)
	)
	@utils.trigger_typing
	async def emblazon(self, ctx, user : converters.MemberOrUser = None):
		
		user = user or ctx.author

		emblazon = await utils.fetchone(
			ctx.bot.dbc, "SELECT * FROM emblazons WHERE id == ?;", (user.id,)
		)
		
		if emblazon: 
			embed = embeds.GENERIC.create(f"{user.name}#{user.discriminator}", "", heading = "Emblazon")
			embed.set_footer(text = "Design and emblazon respectively the property of the armiger and artist.")
			
			embed.set_image(url = emblazon[1])
			
			await ctx.send(embed = embed)
		else: raise utils.CustomCommandError(
			"User does not have emblazon",
			"The user you entered exists, but has not specified an emblazon."
		)
		
	@commands.command(
		help = "Generates a coat of arms.\n If using in a DM, it is based on your name and birthday;"\
		" for privacy reasons, it is random otherwise. Based on a chart by Snak and James.",
		aliases = ("gen", "g")
	)
	async def generate(self, ctx):	
		with open("data/generator.json") as file: 
			parts = json.load(file)
		
		results = {}
		tinctures = ("colour", "metal")
		result_tinctures = ("field", "background", "foreground")
				
		if isinstance(ctx.channel, discord.abc.GuildChannel):
			for category in parts.keys():
				if category in ("colour", "metal", "fur"): continue
				results[category] = random.choice(list(parts[category].values()))
			
			if bool(random.getrandbits(1)): 
				tinctures = tinctures[::-1]
			
			for i, result in enumerate(result_tinctures):
				tincture = tinctures[0] if i % 2 else tinctures[1]
				if tincture == "colour" and random.randrange(10) == 5: tincture = "fur"
				
				results[result] = random.choice(list(parts[tincture].values()))
		else:
			def get_letter_val(letter, category):
				for letters, value in category.items():
					if letter.upper() in letters: return value
				raise utils.BadMessageResponse("Invalid value")
			
			message = await responses.respond_or_react(
				ctx,
				"This command generates a blazon from a few details. React with :x: to cancel.\n"\
				"To start with, give me a short name of a **day**, then a **month**, like 8 Apr.",
				added_check = lambda m: m.content in parts["charge"].keys()
			)
			results["charge"] = parts["charge"][message.content]
			
			await ctx.send("Okay. Now tell me the **first letter** of a **first name**.")
			message = await responses.check(ctx, lambda m: len(m.content) == 1 and m.content.isalpha())
			results["ordinary"] = get_letter_val(message.content, parts["ordinary"])
				
			await ctx.send("Great. Now tell me the **amount** of letters in that person's **last name**.")
			message = await responses.check(ctx, lambda m: m.content.isnumeric())
			
			if int(message.content) % 2 == 0: 
				tinctures = tinctures[::-1]
				
			await ctx.send("Thanks! Now, give me the **first three letters** of that **last name**.")
			message = await responses.check(ctx, lambda m: len(m.content) == 3 and m.content.isalpha())
			letters = message.content
			
			await ctx.send("And finally, give me the **last two letters** of the **first name**.")
			message = await responses.check(ctx, lambda m: len(m.content) == 2 and m.content.isalpha())
			letters += message.content
			pos = -1
			
			for i, result in enumerate(result_tinctures):
				pos = 4 if i == 2 else pos + 1
				tincture = tinctures[0] if i % 2 else tinctures[1]
				
				if tincture == "colour":
					adjacent = pos - 1 if pos == 4 else pos + 1
					if letters[adjacent] == letters[pos]: 
						tincture = "fur"
						pos = adjacent 
				
				results[result] = get_letter_val(letters[pos], parts[tincture])
			
		embed = embeds.GENERIC.create("", "", heading = "Generated blazon")		
		embed.set_footer(text = "Generator based on a chart by Snak and James.")
		
		embed.title = f"*{results['field'].capitalize()}, on {utils.pronounise(results['ordinary'])}"\
					  f" {results['background']} {utils.pronounise(results['charge'].lower())}"\
					  f" {results['foreground']}*"
		
		await ctx.send(embed = embed)
		
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
		help = "Looks up heraldic terms using the DrawShield API.\nTerms are sourced from"\
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
		help = "Generates a motto randomly.\n"\
			   "The included functionality has several advancements over previous"\
		       "motto generators.",
		aliases = ("mt", "mot")
	)
	@utils.trigger_typing
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
		motto = re.sub(self.MOTTO_PARTS, chooseTerm, template).capitalize()		
		
		await ctx.send(embed = embeds.GENERIC.create(f"{motto}", "", heading = "Motto generator"))
		
	@commands.command(
		help = "Randomly selects a motto from a list of over 400.\n"\
		"These include countries, heads of state, and universities",
		aliases = ("rmot", "rm")
	)
	async def randmotto(self, ctx):
		with open("data/mottoes.csv") as file:
			row = random.choice(list(csv.reader(file, delimiter=";")))
					
		embed = embeds.SEARCH_RESULT.create(
			f"{row[1]}",
			f"**{row[0]}**",
			heading = "Random motto"
		)	
		
		if row[2].strip(" ") != "English":
			embed.description += f"\n*{row[3].strip(' ')}* ({row[2].strip(' ')})"	
					
		await ctx.send(embed=embed)
		
	@commands.command(
		help = "Provides links to a number of heraldic resources.\n"\
			   "Retrieves information from Novov's Heraldic Resources."
			   " If no resource name is given, lists available resources.",
		aliases = ("re", "source", "resources", "r")
	)
	@utils.trigger_typing
	async def resource(self, ctx, source = None):
		html = await utils.get_text(
			ctx.bot.session, 
			"https://novov.me/linkroll/resources.html?bot",
			encoding = "UTF-8"
		)
		results = await self.bot.loop.run_in_executor(None, re.findall, self.RESOURCE, html)
		resources = { r[0]: r for r in results }
		
		def resource_result(resource):
			embed = embeds.GENERIC.create(
				re.sub(self.RES_SUB_A, "*", resource[2]),
				re.sub(self.RES_SUB_B, "", resource[3]),
				heading = "Resource"
			)
			embed.url = resource[1]
			return embed
		
		if not source:
			embed = embeds.GENERIC.create(
				"", 
				f"- `random`: Choose a random resource.\n", 
				heading = "Resources list"
			)
			for name, resource in resources.items():
				embed.description += f" - `{name}`: {re.sub(self.RES_SUB_A, '*', resource[2])}\n"
				
			embed.description += "[Full list](https://novov.me/linkroll/resources.html?bot)"
		elif source == "random":
			embed = resource_result(random.choice(resources))
		else:
			if source not in resources:
				raise utils.CustomCommandError(
					"Nonexistent resource",
					"Type `!resources` to see a list of resources."
				)
				
			embed = resource_result(resources.get(source)) 
		
		embed.set_footer(text = f"Retrieved from Novov's Heraldic Resources.")		
		await ctx.send(embed = embed)
		
	@commands.command(
		help = "Sets the emblazon of your arms shown by `!emblazon`."\
			   "\nThis is associated with your Discord ID. If no value is provided, deletes any extant emblazon.",
		aliases = ("se", "delemblazon", "de")
	)
	@utils.trigger_typing
	async def setemblazon(self, ctx, url : typing.Optional[converters.Url] = None):	
		if not url and len(ctx.message.attachments) > 0:
			url = ctx.message.attachments[0].url
						
		if url:
			await self.bot.dbc.execute(
				"INSERT INTO emblazons (id, url) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET url = ?;",
				(ctx.author.id, url, url)
			)
			await self.bot.dbc.commit()
			await ctx.send(":white_check_mark: | Emblazon updated.")
			
			return
		
		if not await utils.fetchone(self.bot.dbc, "SELECT * FROM emblazons WHERE id = ?;", (ctx.author.id,)): 
			raise utils.CustomCommandError(
				"User does not have emblazon",
				"You do not have an emblazon to remove."
			)
		
		await self.bot.dbc.execute(
			"DELETE FROM emblazons WHERE id = ?;",
			(ctx.author.id,)
		)
		await self.bot.dbc.commit()
		await ctx.send(":x: | Emblazon removed.")
		
	@commands.command(
		help = "Shows a list of commonly used tinctures.",
		aliases = ("t", "colours", "colors", "metals", "furs")
	)
	@utils.trigger_typing
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
	bot.add_cog(HeraldicStuff(bot))