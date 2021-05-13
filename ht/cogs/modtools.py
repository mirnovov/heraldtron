import discord, asyncio, typing, re
from discord.ext import commands
from datetime import datetime
from .. import utils, embeds

class ModerationTools(commands.Cog, name = "Moderation"):
	MAX_FEEDS = 3
	SR_VAL = re.compile("(r\/|\/|r\/)+")
	
	def __init__(self, bot):
		self.bot = bot
		
	#right now, just a bodge of has_role, but expand this so it works in dm, by checking all valid servers under that circumstance
	#also allow bot owner do access certain commands to prevent abuse
	async def cog_check(self, ctx):
		item = "Herald"
		if not isinstance(ctx.channel, discord.abc.GuildChannel):
			raise commands.NoPrivateMessage()

		if isinstance(item, int):
			role = discord.utils.get(ctx.author.roles, id=item)
		else:
			role = discord.utils.get(ctx.author.roles, name=item)
		if role is None:
			raise commands.MissingRole(item)
		return True
		
	@commands.command(
		help = "Adds a Reddit feed for the given query and channel.\nSearches use Reddit syntax;"\
			   " for instance, `flair:novov` gets posts flaired `novov`."\
			   " Feeds get the newest 8 posts every 2 hours.", 
		aliases = ("af", "feed")
	)	
	async def addfeed(self, ctx, subreddit : str, channel : discord.TextChannel, search_query : str):
		rowcount = await utils.fetchone(self.bot.dbc, "SELECT COUNT(*) FROM reddit_feeds")
		
		if rowcount[0] > self.MAX_FEEDS:
			raise utils.CustomCommandError("Excessive feed count", f"A server cannot have more than 3 feeds.")
		
		subreddit = re.sub(self.SR_VAL, "", subreddit)
		validate = await utils.get_json(self.bot.session, f"https://www.reddit.com/r/{subreddit}/new.json?limit=1")
		
		if validate.get("error"): raise utils.CustomCommandError(
			"Invalid subreddit",
			f"**r/{subreddit}** either does not exist or is inaccessible."
		)
		elif validate["data"]["dist"] > 0:
			newest = validate["data"]["children"][0]["data"]["name"] #json can be a nightmare
		else: newest = None
		
		await self.bot.dbc.execute(
			"INSERT INTO reddit_feeds VALUES (?, ?, ?, ?, ?, ?);",
			(None, ctx.guild.id, channel.id, subreddit, search_query, newest)
		)
		await self.bot.dbc.commit()
		await ctx.send(":white_check_mark: | Subreddit feed created.")
	
	@commands.command(
		help = "Shows current Reddit feeds and allows deleting them.", 
		aliases = ("managefeed", "mf", "feeds")
	)	
	async def delfeed(self, ctx):
		query = await self.bot.dbc.execute("SELECT * FROM reddit_feeds WHERE guild = ?", (ctx.guild.id,))
		feeds = await query.fetchmany(size = self.MAX_FEEDS)
		
		embed = embeds.FEED.create("", "\n\u200B\n", heading = f"Feeds for {ctx.guild.name}")
		emojis = ("\U0000274C","\U0001F98A", "\U0001F428", "\U0001fF42E")[:len(feeds) + 1]
		
		for i, feed in enumerate(feeds, start = 1):
			channel = (self.bot.get_channel(feed[2]) or await self.bot.fetch_channel(feed[2])).mention or "**invalid**"
			embed.description += f"- {emojis[i]} **r/{feed[3]}** to {channel} (query: *{feed[4]}*)\n"
		
		embed.description += "\nReact with an emoji to delete a feed, or :x: to cancel."
		message = await ctx.send(embed = embed)
		await utils.add_multiple_reactions(message, emojis)
		
		def check_react(reaction, user):
			if ctx.author != user: return False
			return reaction.message == message and reaction.emoji in emojis 
		
		try:
			reaction, user = await ctx.bot.wait_for("reaction_add", timeout = 150, check = check_react)		
		except asyncio.TimeoutError: 
			raise await utils.CommandCancelled.create("Command timed out", ctx)
		
		if reaction.emoji == emojis[0]:
			raise await utils.CommandCancelled.create("Command cancelled", ctx)
		else:
			await self.bot.dbc.execute(
				"DELETE FROM reddit_feeds WHERE id = ?;", 
				(feeds[emojis.index(reaction.emoji) - 1][0],)
			)
			
			await self.bot.dbc.commit()
			await ctx.send(":x: | Subreddit feed deleted.")
	
	@commands.command(
		help = "Displays a moderator message in a channel.\n By default, this is"\
		" the channel the command is invoked in, but it can be specified beforehand.",
		aliases = ("m",)
	)
	async def modmessage(self, ctx, channel : typing.Optional[discord.TextChannel] = None, *, message_content):
		channel = channel or ctx.channel
	
		embed = embeds.MOD_MESSAGE.create(message_content, "")
		embed.set_footer(
			text=f"Sent by {ctx.author.display_name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url=ctx.author.avatar_url_as(size=256)
		)

		await channel.send(embed=embed)
	
	@commands.command(help = "Locks a channel, disabling the ability to send messages from it.", aliases = ("l",))	
	async def lock(self, ctx, channel : typing.Optional[discord.TextChannel] = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=False)
		await ctx.send(f":lock: | **{ctx.channel.mention} has been locked.**")
		
	@commands.command(help = "Enables/disables welcome and leave messages for a server.", aliases = ("wl", "welcome", "ms", "message"))	
	async def messages(self, ctx, enabled : bool):
		enabled_int = int(enabled)
		enabled_text = "enabled" if enabled else "disabled"
		 
		await self.bot.dbc.execute("UPDATE guilds SET welcome_users = ? WHERE discord_id = ?",(enabled_int, ctx.guild.id))
		await self.bot.dbc.commit()
		await ctx.send(f":envelope_with_arrow: | Welcome and leave messages have been **{enabled_text}** for this server.")
	
	@commands.command(help = "Sets the leave message for this server.", aliases = ("sl", "setl"))	
	async def setleave(self, ctx):
		await self.set_message(ctx, True)
		
	@commands.command(help = "Sets the welcome message for this server.", aliases = ("sw", "setw"))	
	async def setwelcome(self, ctx):
		await self.set_message(ctx, False)
		
	@commands.command(help = "Unlocks a channel, restoring the ability to send messages from it.",aliases=("ul",))	
	async def unlock(self, ctx, channel : discord.TextChannel = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=True)
		await ctx.send(f":unlock: | **{ctx.channel.mention} has been unlocked.**")
		
	async def set_message(self, ctx, leave):
		enabled = await self.bot.dbc.execute("SELECT welcome_users FROM guilds WHERE discord_id == ?;",(ctx.guild.id,))
		
		if enabled == 0: raise utils.CustomCommandError(
			"Welcome and leave messages disabled",
			"Your message cannot be set, as the welcome and leave message functionality"\
			" is currently not operational. Turn it on with `!messages yes`."
		)
			
		result = await utils.respond_or_react(
			ctx,
			"Either type your message below, react with :leftwards_arrow_with_hook:"\
			" to revert to the default, or with :x: to cancel.\n"\
			"To include details, use `GUILD_NAME`, `MENTION`, or `MEMBER_NAME`.",
			["\U000021A9\U0000FE0F"]
		)
		
		if isinstance(result, discord.Message) or result[0].emoji == "\U000021A9\U0000FE0F":
			message_type = "welcome_text" if not leave else "leave_text"
			new = None if isinstance(result, tuple) else result.content
			
			await self.bot.dbc.execute(f"UPDATE guilds SET {message_type} = ? WHERE discord_id = ?;",(new, ctx.guild.id))
			await self.bot.dbc.commit()
			await ctx.send(":white_check_mark: | Message changed.")
		
def setup(bot):
	bot.add_cog(ModerationTools(bot))