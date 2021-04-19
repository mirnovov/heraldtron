import discord, typing, asyncio, random, aiohttp, os
from discord.ext import commands
from dotenv import load_dotenv
from .. import utils

class MiscStuff(commands.Cog, name="Miscellaneous"):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(
		help="Chooses a random number.\n"\
		" By default, this is out of 6, but another value can be specified.",
		aliases=("dice","d")
	)
	async def roll(self, ctx, ceiling : typing.Optional[int] = 6):
		if ceiling < 2 or ceiling > 9999:
			await ctx.send(embed=utils.nv_embed(
				"Incorrect roll ceiling",
				"The value specified must be between 2 and 9999."
			))
			return
		
		message = await ctx.send(":game_die: | Rolling the dice...")
		result = random.randrange(1, ceiling + 1)
		await asyncio.sleep(2)
		await message.edit(content=f":game_die: | The dice landed on... **{result}**!")
		
	@commands.command(
		help="Completes a passage of text using machine learning.\n"\
		" This uses DeepAI's online model to compute the result.",
		aliases=("aitext","tg")
	)
	@commands.before_invoke(utils.typing)
	async def textgen(self, ctx, *, text : str):
		url = "https://api.deepai.org/api/text-generator"
		data = {"text": text.strip()}
		headers = {"api-key": os.environ["DEEP_AI"].strip()}
			
		async with aiohttp.ClientSession() as session:
			load_dotenv()
			async with session.post(url,data=data,headers=headers) as source:
				if not source.ok:
					await ctx.send(embed=utils.nv_embed(
						"Invalid HTTP request",
						f"Please try again. If problems persist, contact the bot's maintainer."
					))
					return
				result_json = await source.json()
		
		result = result_json["output"]	
		newtext = result[result.index(text) + len(text):]
		
		await ctx.send(f":abcd: | **Text generated!**\n\n*{text}*{newtext}")
		
def setup(bot):
	bot.add_cog(MiscStuff(bot))