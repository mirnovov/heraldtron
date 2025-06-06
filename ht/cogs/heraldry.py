import discord, csv, json, random, re
from discord import app_commands
from discord.ext import commands
from .. import converters, embeds, modals, services, utils, views
from ..artifacts import Source

class HeraldryMisc(utils.MeldedCog, name = "General", category = "Heraldry"):
	MOTTO_PARTS = re.compile("([&|!]\\w\\w\\w)")
	RAND_SUB = re.compile("\n|\t| {2,}")
	
	ARTIFACT_CHOICES = [a.choice for a in Source.register.values()]
	CHALLENGE_CHOICES = [
		app_commands.Choice(name = "The Book of Public Arms", value = "public"),
		app_commands.Choice(name = "Wikimedia Commons", value = "wikipedia"),
		app_commands.Choice(name = "coadb", value = "coadb")
	]
	
	def __init__(self, bot):
		self.bot = bot

	@commands.hybrid_command(
		help = "Displays a random historical heraldic artifact.\n"
			"This can be narrowed down to an individual source:\n\n"
			f"{Source.str_list()}",
		aliases = ("ar", "relic")
	)
	@app_commands.choices(source = ARTIFACT_CHOICES)
	@app_commands.describe(source = "The source to use for artifacts. By default, all artifacts are used.")
	@utils.trigger_typing
	async def artifact(self, ctx, source: str = "all"):
		if type(source) == app_commands.Choice:
			source = source.value
		
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
		title = discord.utils.escape_markdown(result[1])

		embed = embeds.SEARCH_RESULT.create(title, result[2], heading = "Random artifact")
		embed.url = result[0]
		embed.set_footer(text = f"{result[4]} via {museum.desc}" if result[4] else museum.desc)

		if result[3]: embed.set_image(url = result[3])

		await ctx.send(embed = embed)

	@commands.hybrid_command(
		name = "catalog",
		help = "Looks up a term in DrawShield's repository of charges.\nCode © Karl Wilcox",
		aliases = ("charge", "ca")
	)
	@app_commands.describe(charge = "The heraldic charge to look up.")
	@utils.trigger_typing
	async def ds_catalog(self, ctx, *, charge):
		catalog = await services.ds_catalog(self.bot.session, charge)

		if catalog == None: raise utils.CustomCommandError(
			"Invalid catalog item",
			"Check your spelling and try again."
		)

		embed = embeds.SEARCH_RESULT.create(
			f"Catalog entry for \"{charge}\"",
			catalog[1] if len(catalog) > 1 else "",
			heading = "DrawShield catalog"
		)
		embed.set_image(url = catalog[0])
		embed.set_footer(
			icon_url = "https://drawshield.net/img/shop-logo.png",
			text = f"Retrieved using DrawShield; © Karl Wilcox. "
		)

		await ctx.send(embed=embed)

	@commands.hybrid_command(
		name = "challenge",
		help = "Displays a random image to emblazon using DrawShield.\nThis uses the DrawShield API. Code © Karl Wilcox; images © coadb,"
			   " The Book of Public Arms, Wikimedia Commons contributors (individual sources"
			   " can be selected via *coadb*, *public*, and *wikipedia* respectively).",
		aliases = ("ch", "cl")
	)
	@app_commands.choices(source = CHALLENGE_CHOICES)
	@app_commands.describe(source = "The source to use for challenges.")
	@utils.trigger_typing
	async def ds_challenge(self, ctx, source: app_commands.Choice[str] = "all"):
		if type(source) == app_commands.Choice:
			source = source.value
		
		url = await utils.get_json(self.bot.session, f"https://drawshield.net/api/challenge/{source}")

		if isinstance(url, dict) and "error" in url:
			raise utils.CustomCommandError(
				"Invalid challenge category",
				f"Type `{ctx.clean_prefix}help challenge` to see the available categories."
			)

		embed = embeds.GENERIC.create("", "Try emblazoning this using DrawShield!", heading = "Random image")
		embed.url = url
		embed.set_footer(text = "Retrieved using DrawShield; © Karl Wilcox. ")

		if url.startswith("https://commons.wikimedia.org"):
			result = await services.commons(
				self.bot.session, self.bot.loop, url.removeprefix("https://commons.wikimedia.org//wiki/")
			)
			embed.set_image(url = result.find("urls").find("thumbnail").text)

		else: embed.set_image(url = url)

		await ctx.send(embed = embed)

	@commands.hybrid_command(
		help = "Illustrates arms using DrawShield.\nNote that DrawShield does not support"
			   " all possible blazons. Code © Karl Wilcox",
		aliases = ("drawshield",)
	)
	@app_commands.describe(blazon = "The blazon to illustrate. The language differs slightly from proper blazonry.")
	@utils.trigger_typing
	async def ds(self, ctx, *, blazon : str):
		embed, file = await services.ds(self.bot.session, blazon, "Shield")
		await ctx.send(embed = embed, file = file)

	@commands.hybrid_command(
		help = "Generates a coat of arms based on personal details. These won't be stored by the bot."
			   "\nBased on a chart by Snak and James.",
		aliases = ("gen", "g")
	)
	async def generate(self, ctx):
		await modals.show(
			ctx, modals.GeneratorModal(), "Generate",
			f"The `generate` function creates arms based on a [chart](<{modals.GeneratorModal.CHART_URL}>)"
			" by Snak and James. The details you use won't be stored by this bot."
		)

	@commands.hybrid_command(
		help = "Generates a motto randomly.\nThe included functionality has several"
			   " advancements over previous motto generators.",
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

	@commands.hybrid_command(
		help = "Randomly selects a motto from a list of over 400.\n"
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

	@commands.hybrid_command(
		name = "random",
		help = "Generates random arms using DrawShield.\nCode © Karl Wilcox.",
		aliases = ("ra",)
	)
	@utils.trigger_typing
	async def ds_random(self, ctx):
		blazon = await utils.get_text(self.bot.session, "https://drawshield.net/include/randomblazon.php")
		blazon = re.sub(self.RAND_SUB, " ", blazon.removesuffix("// created by Drawshield.net/random\n")).strip()

		embed, file = await services.ds(self.bot.session, blazon, "Random shield")
		await ctx.send(embed = embed, file = file)

	@commands.hybrid_command(
		help = "Render arms using Heraldicon.",
		aliases = ("heraldicon",)
	)
	@app_commands.describe(blazon = "The blazon to illustrate. The language differs slightly from proper blazonry.")
	@utils.trigger_typing
	async def hd(self, ctx, *, blazon : str):
		embed, file = await services.heraldicon(self.bot.session, blazon)
		await ctx.send(embed = embed, file = file)

	@commands.hybrid_command(
		help = "Show rendering options that can be used with Heraldicon.",
		aliases = ("heraldicon_options",)
	)
	@utils.trigger_typing
	async def hd_options(self, ctx):
		embed = await services.heraldicon_options(self.bot.session)
		await ctx.send(embed = embed)


async def setup(bot):
	await bot.add_cog(HeraldryMisc(bot))
