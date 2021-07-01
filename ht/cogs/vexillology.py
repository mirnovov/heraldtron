import discord, asyncio, csv, random 
from discord.ext import commands
from ..ext import OnlineSeych
from .. import embeds, services, utils, views

class VexStuff(utils.MeldedCog, name = "Vexillology", category = "Vexillology"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help = "Finds the results of `flag [query]` using Google Images.",
		aliases = ("fs",)
	)
	@utils.trigger_typing
	async def flagsearch(self, ctx, *, query):
		await services.gis(ctx, "flag " + query)
		
	@commands.command(
		help = "Illustrates flags using DrawShield.\nNote that DrawShield does not support"
			   " all possible flags, and the vexillological functionality is still in early"
			   " development. Code © Karl Wilcox",
		aliases = ("df",)
	)
	@utils.trigger_typing
	async def drawflag(self, ctx, *, blazon : str):
		embed, file = await services.ds(self.bot.session, blazon + " in flag shape", "Flag")
		await ctx.send(embed = embed, file = file)
		
	@commands.command(
		help = "Displays a random flag fact from a list of 38 facts.\n"
			   " Facts contributed by Miner, Capitalism, czechmate, Boatswain,"
			   " DiamondMinotaur, Judah, Ohsama, and FrancisH.",
		aliases = ("flagfacts", "ff")
	)
	async def flagfact(self, ctx, *, fid : int = -1):
		with open("data/flagfacts.csv") as file:
			next(file)
			facts = list(csv.reader(file, delimiter = ";"))
			
			if fid > len(facts):
				raise utils.CustomCommandError(
					"Flag fact is nonexistent",
					"The number you entered is too high. Currently, there"
					f" are only {len(facts)} flag facts."
				)
			
		fact = random.choice(facts) if fid < 0 else facts[fid] 			
		embed = embeds.FLAG_FACT.create(f"{fact[1]}", "", heading = f"Flag fact #{fact[0]}")	
		
		await ctx.send(embed=embed)
	
	@commands.command(help="Displays a guide to various flag ratios.")
	async def ratios(self, ctx):
		embed = embeds.GENERIC.create("", "", heading = "Flag ratios")
		embed.set_image(url = "https://i.imgur.com/qMGrKqs.png")
		embed.set_footer(text = "Infographic by /u/greatpaperwolf")
		await ctx.send(embed = embed)
	
	@commands.command(
		help = "Seychelles-izes a flag.\nUses Akshay Chitale's Seychelles Flag Generator script.",
		aliases = ("sy", "seych")
	)
	@utils.trigger_typing	
	async def seychelles(self, ctx):
		img_check = lambda m: len(m.attachments) > 0 and m.attachments[0].content_type.startswith("image") 
		result = await views.RespondOrReact(ctx, added_check = img_check).run(
			"What image would you like me to seychelles-ize?\n"
			"Respond with a picture of a flag below.\n",
		)
				
		image_url = result.attachments[0].url
		image_content = await utils.get_bytes(ctx.bot.session, image_url)
		image = await self.bot.loop.run_in_executor(None, OnlineSeych.generate, image_url, image_content)
		file = discord.File(image, filename = "seychelles.png")
		
		embed = embeds.GENERIC.create("Result", "", heading = "Seychelles-izer")
		embed.set_image(url = "attachment://seychelles.png")
		embed.set_footer(text = "Original script by Akshay Chitale")
		await ctx.send(embed = embed, file = file)

def setup(bot):
	bot.add_cog(VexStuff(bot))