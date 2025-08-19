import discord, asyncio, csv, random
from discord import app_commands, ui
from discord.ext import commands
from ..ext import OnlineSeych
from .. import services, utils, views

class VexStuff(utils.MeldedCog, name = "Vexillology", category = "Vexillology"):
	def __init__(self, bot):
		self.bot = bot

	@commands.hybrid_command(
		help = "Finds the results of `flag [query]` using Google Images.",
		aliases = ("flagsearch",)
	)
	@app_commands.describe(query = "The search query to use.")
	@utils.trigger_typing
	async def fs(self, ctx, *, query):
		await services.gis(ctx, "flag " + query)

	@commands.hybrid_command(
		help = "Illustrates flags using DrawShield.\nNote that DrawShield does not support"
			   " all possible flags, and the vexillological functionality is still in early"
			   " development. Code © Karl Wilcox",
		aliases = ("drawflag",)
	)
	@app_commands.describe(blazon = "The blazon to illustrate. The language differs slightly from proper blazonry.")
	@utils.trigger_typing
	async def df(self, ctx, *, blazon : str):
		view, file = await services.ds(self.bot.session, blazon + " in flag shape", "Flag")
		await ctx.send(view = view, file = file)

	@commands.hybrid_command(
		help = "Displays a random flag fact from a list of 38 facts.\n"
			   " Facts contributed by Miner, Capitalism, czechmate, Boatswain,"
			   " DiamondMinotaur, Judah, Ohsama, and FrancisH.",
		aliases = ("flagfacts", "ff")
	)
	@app_commands.describe(factid = "The ID of the fact to show. If omitted, a random fact will be chosen.")
	async def flagfact(self, ctx, *, factid : int = -1):
		with open("data/flagfacts.csv") as file:
			next(file)
			facts = list(csv.reader(file, delimiter = ";"))

			if factid > len(facts):
				raise utils.CustomCommandError(
					"Flag fact is nonexistent",
					"The number you entered is too high. Currently, there"
					f" are only {len(facts)} flag facts."
				)

		fact = random.choice(facts) if factid < 0 else facts[factid]
		view = views.Generic(f"{fact[1]}", "", heading = f":triangular_flag_on_post: Flag fact #{fact[0]}")

		await ctx.send(view = view)

	@commands.hybrid_command(help="Displays a guide to various flag ratios.")
	async def ratios(self, ctx):
		view = views.Generic("", "", heading = ":triangular_ruler: Flag ratios")
		view.add_image("https://i.imgur.com/qMGrKqs.png")
		view.add_footer("Infographic by /u/greatpaperwolf")
		await ctx.send(view = view)

	@commands.hybrid_command(
		help = "Seychelles-ises a flag.\nUses Akshay Chitale's Seychelles Flag Generator script.",
		aliases = ("sy", "seych")
	)
	@utils.trigger_typing
	@app_commands.describe(image = "The image to Seychelles-ise.")
	async def seychelles(self, ctx, image: discord.Attachment):
		image_url = image.url
		image_content = await utils.get_bytes(ctx.bot.session, image_url)
		image = await self.bot.loop.run_in_executor(None, OnlineSeych.generate, image_url, image_content)
		file = discord.File(image, filename = "seychelles.png")

		view = views.Generic("Result", "", heading = ":flag_sc: Seychelles-izer")
		view.add_image("attachment://seychelles.png")
		view.add_footer("Original script by Akshay Chitale")
		await ctx.send(view = view, file = file)

async def setup(bot):
	await bot.add_cog(VexStuff(bot))
