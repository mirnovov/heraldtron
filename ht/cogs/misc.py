import discord, typing, asyncio, random
from discord.ext import commands
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
		
def setup(bot):
	bot.add_cog(MiscStuff(bot))