import discord, asyncio, typing, random, os
from discord import app_commands, ui
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from .. import converters, embeds, modals, services, utils, views

class MiscStuff(utils.MeldedCog, name = "Miscellaneous", category = "Other", limit = True):
	TRIVIA_CHOICES = [
		app_commands.Choice(name = "General Knowledge", value = 9),
		app_commands.Choice(name = "Entertainment: Books", value = 10),
		app_commands.Choice(name = "Entertainment: Film", value = 11),
		app_commands.Choice(name = "Entertainment: Music", value = 12),
		app_commands.Choice(name = "Entertainment: Musicals & Theatres", value = 13),
		app_commands.Choice(name = "Entertainment: Television", value = 14),
		app_commands.Choice(name = "Entertainment: Video Games", value = 15),
		app_commands.Choice(name = "Entertainment: Board Games", value = 16),
		app_commands.Choice(name = "Science & Nature", value = 17),
		app_commands.Choice(name = "Science: Computers", value = 18),
		app_commands.Choice(name = "Science: Mathematics", value = 19),
		app_commands.Choice(name = "Mythology", value = 20),
		app_commands.Choice(name = "Sports", value = 21),
		app_commands.Choice(name = "Geography", value = 22),
		app_commands.Choice(name = "History", value = 23),
		app_commands.Choice(name = "Politics", value = 24),
		app_commands.Choice(name = "Art", value = 25),
		app_commands.Choice(name = "Celebrities", value = 26),
		app_commands.Choice(name = "Animals", value = 27),
		app_commands.Choice(name = "Vehicles", value = 28),
		app_commands.Choice(name = "Entertainment: Comics", value = 29),
		app_commands.Choice(name = "Science: Gadgets", value = 30),
		app_commands.Choice(name = "Entertainment: Japanese Anime & Manga", value = 31),
		app_commands.Choice(name = "Entertainment: Cartoon & Animations", value = 32),
	]
	
	ACTIVITIES = {
		-1: "",
		0: "Playing",
		1: "Streaming",
		2: "Listening to",
		3: "Watching",
		4: "Activity:",
		5: "Competing in"
	}

	def __init__(self, bot):
		self.bot = bot

	@commands.hybrid_command(
		help = "Generates a continuously updated countdown post.",
		aliases = ("time", "cd")
	)
	@app_commands.describe(elapsed = "The date to count down to.")
	async def countdown(self, ctx, *, elapsed : converters.Date):
		delta = (elapsed - datetime.now(tz = timezone.utc)) + timedelta(minutes = 1)
		embed = embeds.COUNTDOWN.create(f"<t:{elapsed.timestamp():.0f}:R>", "")
		embed.add_field(name = "End time", value = f"<t:{elapsed.timestamp():.0f}:F>")

		if delta.total_seconds() < 0:
			raise utils.CustomCommandError(
				"Date has already occured",
				"The date that you entered is in the past."
			)

		await ctx.send(embed = embed)

	@commands.hybrid_command(
		help = "Generates a competition distribution. This won't be visible to other users.",
		aliases = ("dt", "dist")
	)
	async def distribute(self, ctx):
		await modals.show(
			ctx, modals.DistributionModal(), "Generate",
			f"The `distribute` function generates a competition distribution."
		)

	@commands.hybrid_command(help = "Conducts a search using Google Images.", aliases = ("img", "gi"))
	@app_commands.describe(query = "The search query to use.")
	@utils.trigger_typing
	async def imgsearch(self, ctx, *, query):
		await services.gis(ctx, "" + query)

	@commands.hybrid_command(
		help = "Chooses a random number.\n"
		" By default, this is out of 6, but another value can be specified.",
		aliases = ("dice", "d")
	)
	@app_commands.describe(ceiling = "The amount of sides on the die to roll. Defaults to six.")
	async def roll(self, ctx, ceiling : commands.Range[int, 2, 9999] = 6):
		message = await ctx.send(":game_die: | Rolling the dice...")
		result = random.randrange(1, ceiling + 1)
		await asyncio.sleep(2)
		await message.edit(content=f":game_die: | The dice landed on... **{result}**!")

	@commands.hybrid_command(help = "Sends a post as the bot user. Handy for jokes and such.", aliases = ("st",), hidden = True)
	@app_commands.default_permissions(create_events = True) #bit of a hack lol
	@app_commands.describe(message_content = "The message to send.")
	@commands.is_owner()
	async def sendtext(ctx, channel : typing.Optional[discord.TextChannel] = None, *, message_content):
		channel = channel or ctx.channel
		await channel.send(message_content)

	@commands.group(
		invoke_without_command = True,
		name = "trivia",
		help = "Asks a trivia question that users can react to.\n"
			   "Optionally, a numeric category can be specified."
			   "\nCourtesy of the Open Trivia Database.\n\u0020\n",
		aliases = ("q","tr")
	)
	@utils.trigger_typing
	async def legacy_trivia(self, ctx, category : typing.Optional[int] = -1):
		catstring = "" if category == -1 else f"&category={category}"
		json = f"https://opentdb.com/api.php?amount=1{catstring}"
		result = await utils.get_json(self.bot.session, json)

		if result["response_code"] == 1:
			raise utils.CustomCommandError(
				"Invalid category code",
				f"Consult `{ctx.clean_prefix}trivia categories` to see the available codes."
			)

		await services.trivia(ctx, None, result["results"][0])

	@legacy_trivia.command(help = "Lists all categories.")
	async def categories(self, ctx):
		result = await utils.get_json(self.bot.session, f"https://opentdb.com/api_category.php")
		embed = embeds.GENERIC.create(
			"Trivia categories", "To choose a category, specify its numeric ID.", heading = "Trivia"
		)

		for category in result["trivia_categories"]:
			embed.add_field(name = category["name"], value=category["id"], inline=True)
	
		embed.set_footer(text = f"Courtesy of the Open Trivia Database.")
		await ctx.send(embed = embed)
	
	@app_commands.command(description = "Asks a trivia question that users can guess.")
	@app_commands.choices(category = TRIVIA_CHOICES)
	@app_commands.describe(category = "The topic that questions will be about. Defaults to all questions.")
	async def trivia(self, interaction, category : app_commands.Choice[int] = -1):
		catstring = "" if category == -1 else f"&category={category.value}"
		json = f"https://opentdb.com/api.php?amount=1{catstring}"
		result = await utils.get_json(self.bot.session, json)
		
		await services.trivia(None, interaction, result["results"][0])

	@commands.hybrid_command(help = "Looks up a Discord user.", aliases = ("u",))
	@app_commands.describe(user = "The user to look up. Defaults to the command sender.")
	@utils.trigger_typing
	async def user(self, ctx, *, user : converters.MemberOrUser = None):
		user = user or ctx.author

		if not isinstance(user, discord.Member) and ctx.guild:
			user = ctx.guild.get_member(user.id) or user

		embed = embeds.USER_INFO.create(user, f"{user.mention}")
		if user.bot:
			embed.description += " | **Bot**"

		embed.set_thumbnail(url = user.display_avatar.with_size(512).url)
		embed.add_field(name = "Created", value = utils.stddate(user.created_at), inline = True)
		embed.description += "\n\u200b"

		if isinstance(user, discord.Member):
			embed.colour = user.colour if user.colour.value != 0 else embeds.DEFAULT

			for activity in user.activities:
				preface = activity.emoji or "" if hasattr(activity, "emoji") else f"**{self.ACTIVITIES[int(activity.type)]}**"
				embed.description += f"\n{preface} {activity.name}"

			embed.add_field(name = "Joined", value = utils.stddate(user.joined_at), inline = True)
			embed.add_field(name = "Status", value = f"Currently **{user.raw_status}**", inline = True)

			if isinstance(ctx.channel, discord.abc.GuildChannel):
				roles = (str(role.mention) for role in user.roles[1:])
				embed.add_field(name = "Roles", value = ", ".join(("@everyone ", *roles)), inline = False)

		await ctx.send(embed = embed)

async def setup(bot):
	await bot.add_cog(MiscStuff(bot))
