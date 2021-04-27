import discord, typing, asyncio, random, aiohttp, os, html
from discord.ext import commands
from .. import utils, services

class MiscStuff(commands.Cog, name="Miscellaneous"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(help="Retrieves a random piece of advice.\nUses evilinsult.com",aliases=("ad",)
	)
	@commands.before_invoke(utils.typing)
	async def advice(self, ctx):			
		result = await utils.get_json(self.bot.session,f"https://api.adviceslip.com/advice",content_type="text/html")
		
		embed = utils.nv_embed(result["slip"]["advice"],"",kind=4,custom_name="Random advice")		
		embed.set_footer(text=f"Retrieved using adviceslip.com")
		await ctx.send(embed=embed)
		
	@commands.command(help="Conducts a search using Google Images.", aliases=("img","gi"))
	@commands.before_invoke(utils.typing)
	async def imgsearch(self, ctx, *, query):
		await services.gis(ctx,"" + query)

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
		
	@commands.command(help="Sends a post as the bot user. Handy for jokes and such.", aliases=("st",), hidden = True)
	@commands.is_owner()	
	async def sendtext(ctx, channel : typing.Optional[discord.TextChannel] = None, *, message_content):
		channel = channel or ctx.channel
		await channel.send(message_content)
		
	@commands.command(
		help="Completes a passage of text using machine learning.\n"\
		" This uses DeepAI's online model to compute the result.",
		aliases=("aitext","tg")
	)
	@commands.before_invoke(utils.typing)
	async def textgen(self, ctx, *, text : str):
		url = "https://api.deepai.org/api/text-generator"
		data = {"text": text.strip()}
		headers = {"api-key": ctx.bot.conf["DEEP_AI"].strip()}
			
		async with ctx.bot.session.post(url,data=data,headers=headers) as source:
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
		
	@commands.group(
		invoke_without_command=True,
		help="Asks a trivia question that users can react to.\n"\
		"Optionally, a numeric category can be specified."\
		"\nCourtesy of the Open Trivia Database.\n\u0020\n",
		aliases=("q","tr")
	)
	@commands.before_invoke(utils.typing)
	async def trivia(self, ctx, category : typing.Optional[int] = -1):
		catstring = "" if category == -1 else f"&category={category}"
		json = f"https://opentdb.com/api.php?amount=1{catstring}"
		result = await utils.get_json(self.bot.session, json)
		
		if result["response_code"] == 1:
			await ctx.send(embed=utils.nv_embed(
				"Invalid category code",
				f"Consult `!trivia categories` to see the available codes."
			))
			return
			
		result = result["results"][0]
		info = f"**{result['category']}** | {result['difficulty'].capitalize()}\n\n"
		embed = utils.nv_embed(html.unescape(result["question"]), info, kind=4, custom_name="Trivia")
		
		if result["type"] == "boolean":
			emojis = ("\U0001f438", "\U0001f430")
			correct = random.randrange(0,2)
		else:
			emojis = ("\U0001f431", "\U0001f436", "\U0001f434", "\U0001f43b")
			correct = random.randrange(0,4)
			
		answers = result["incorrect_answers"]
		answers.insert(correct,result["correct_answer"])
		
		for num, answer in enumerate(answers):
			embed.description += f"- {emojis[num]} {html.unescape(answer)}\n\n"
			
		embed.description += f"React to respond. The correct answer will appear in **one minute.**"
		
		embed.set_footer(text=f"Courtesy of the Open Trivia Database.")
		message = await ctx.send(embed=embed)
		await asyncio.gather(*[message.add_reaction(r) for r in emojis])
		await asyncio.sleep(60)
		
		embed.description = f"{info}The correct answer is: {emojis[correct]}"\
		 					f" **{html.unescape(answers[correct])}**"
		updated = await message.channel.fetch_message(message.id)
		
		if updated is None:
			return #message deleted
			
		if len(updated.reactions) > 0:
			embed.description += "\n\n**Responses:**\n\u0020"
		
		for react in updated.reactions:
			if react.emoji not in emojis or react.count == 1: continue
			
			num = emojis.index(react.emoji)
			user_str = " "
			emoji_str = str(react.emoji)
			
			async for user in react.users():
				if user == ctx.bot.user: continue
				user_str += f"{user.mention},"
				
			embed.description += f"\n- {emoji_str} {answers[num]}: "\
								 f"{user_str.rstrip(',')} (**{react.count - 1}**)\n\u200b"
		
		await message.edit(embed=embed)
			
	@trivia.command(help="Lists all categories.")
	async def categories(self, ctx):
		result = await utils.get_json(self.bot.session, f"https://opentdb.com/api_category.php") 
		embed = utils.nv_embed(
			"Trivia categories","To choose a category, specify its numeric ID.",kind=4,custom_name="Trivia"
		)
		for catkind in result["trivia_categories"]:
			embed.add_field(name=catkind["name"], value=catkind["id"], inline=True)	
			
		embed.set_footer(text=f"Courtesy of the Open Trivia Database.")
		await ctx.send(embed=embed)
			
		
def setup(bot):
	bot.add_cog(MiscStuff(bot))