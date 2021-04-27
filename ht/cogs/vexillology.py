import discord, csv, random, asyncio
from discord.ext import commands
from ..ext import compute_seychelles
from .. import utils, services

class VexStuff(commands.Cog, name="Vexillology"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help="Finds the first result of `flag [query]` using Google Images.",
		aliases=("fs",)
	)
	@commands.before_invoke(utils.typing)
	async def flagsearch(self, ctx, *, query):
		await services.gis(ctx, "flag " + query)
		
	@commands.command(
		help="Illustrates flags using DrawShield.\nNote that DrawShield does not support"\
		" all possible flags, and the vexillological functionality is still in early"\
		" development. Code © Karl Wilcox",
		aliases=("df",)
	)
	@commands.before_invoke(utils.typing)
	async def drawflag(self, ctx, *, blazon : str):
		embed, file = await services.ds(self.bot.session, blazon+" in flag shape", "Flag")
		await ctx.send(embed=embed,file=file)
		
	@commands.command(
		help="Displays a random flag fact from a list of 38 facts.\n"\
		" Facts contributed by Miner, Capitalism, czechmate, Boatswain,"\
		" DiamondMinotaur, Judah, Ohsama, and FrancisH.",
		aliases=("flagfacts",)
	)
	async def flagfact(self, ctx, *, fid : int = -1):
		with open("data/flagfacts.csv") as file:
			next(file)
			facts = list(csv.reader(file, delimiter=";"))
			
			if fid > len(facts):
				await ctx.send(embed=utils.nv_embed(
					"Flag fact is nonexistent",
					"The number you entered is too high. Currently, there"\
					f" are only {len(facts)} flag facts."
				))
				return
			
			fact = random.choice(facts) if fid < 0 else facts[fid] 
					
		embed = utils.nv_embed(
			f"{fact[1]}",
			"",
			kind=3,
			custom_name=f"Flag fact #{fact[0]}",
			custom_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/OOjs_UI_icon_flag-ltr-invert.svg/"\
			"200px-OOjs_UI_icon_flag-ltr-invert.svg.png"
		)	
		
		await ctx.send(embed=embed)
	
	@commands.command(help="Displays a guide to various flag ratios.")
	async def ratios(self, ctx):
		embed = utils.nv_embed("","",kind=4,custom_name="Flag ratios")
		embed.set_image(url="https://i.imgur.com/qMGrKqs.png")
		embed.set_footer(text="Infographic by /u/greatpaperwolf")
		await ctx.send(embed=embed)
	
	@commands.command(
		help="Seychelles-izes a flag.\n"\
			 "Uses Akshay Chitale's Seychelles Flag Generator script.",
		aliases=("sy",)
	)
	@commands.before_invoke(utils.typing)	
	async def seychelles(self,ctx):
		await ctx.send(
			"What image would you like me to seychelles-ize?\n"\
			"Respond with `cancel` to cancel the command. The command will automatically be cancelled in 30 seconds."
		)
		
		def check(message):
			if message.author != ctx.author: return False
			elif message.content == "cancel": return True
				
			return len(message.attachments) > 0 and message.attachments[0].content_type.startswith("image")
		
		try:
			message = await self.bot.wait_for("message", check=check, timeout=30)
		except asyncio.TimeoutError:
			await ctx.send("`seychelles` command timed out.")
			return
			
		if message.content == "cancel": 
			await ctx.send("`seychelles` command cancelled.")
			return
		
		image_url = message.attachments[0].url
		image_content = await utils.get_bytes(ctx.bot.session, image_url)
		image = await self.bot.loop.run_in_executor(None, compute_seychelles, image_url, image_content)
		file = discord.File(image,filename="seychelles.png")
		
		embed = utils.nv_embed("Result","",kind=4,custom_name="Seychelles-izer")
		embed.set_image(url="attachment://seychelles.png")
		embed.set_footer(text="Original script by Akshay Chitale")
		await ctx.send(embed=embed,file=file)

def setup(bot):
	bot.add_cog(VexStuff(bot))