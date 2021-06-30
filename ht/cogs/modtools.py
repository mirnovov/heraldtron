import discord, asyncio, typing, re
from discord.ext import commands
from datetime import datetime
from .. import converters, embeds, responses, utils

class ModerationTools(utils.MeldedCog, name = "Moderation", category = "Moderation", limit = False):
	MAX_FEEDS = 3
	SR_VAL = re.compile("(r\/|\/|r\/)+")
	
	def __init__(self, bot):
		self.bot = bot
		
	async def cog_check(self, ctx):
		if await ctx.bot.is_owner(ctx.author):
			return True
		elif isinstance(ctx.channel, discord.abc.GuildChannel):
			if self.is_mod(ctx.author.guild_permissions):
				return True	
		else:
			for guild in ctx.author.mutual_guilds:
				perms = guild.get_member(ctx.author.id).guild_permissions
				if self.is_mod(perms): return True
		
		raise commands.MissingRole("admin")
	
	@staticmethod	
	def is_mod(perms):
		return perms.manage_channels or perms.manage_guild or perms.administrator
	
	@commands.command(
		help = "Adds a Reddit feed for the given query and channel.\nSearches use Reddit syntax;"
			   " for instance, `flair:novov` gets posts flaired `novov`."
			   " Feeds get the newest 8 posts every 2 hours.", 
		aliases = ("af", "feed")
	)	
	async def addfeed(
		self, ctx, 
		subreddit : str, 
		channel : discord.TextChannel, 
		ping : typing.Optional[bool], 
		search_query : str
	):
		ping = ping or False
		rowcount = await self.bot.dbc.execute_fetchone("SELECT COUNT(*) FROM reddit_feeds")
		
		if rowcount[0] > self.MAX_FEEDS:
			raise utils.CustomCommandError("Excessive feed count", f"A server cannot have more than {self.MAX_FEEDS} feeds.")
		
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
			"INSERT INTO reddit_feeds VALUES (?, ?, ?, ?, ?, ?, ?);",
			(None, (await self.choose_guild(ctx)).id, channel.id, subreddit, int(ping), search_query, newest)
		)
		await self.bot.dbc.commit()
		await ctx.send(":white_check_mark: | Subreddit feed created.")
		
	@commands.command(help = "Creates a new roll channel.", aliases = ("c", "create", "new"))	
	async def channel(self, ctx, user : converters.MemberOrUser, info : converters.RollVariant):
		sorting = self.bot.get_cog("Roll Sorting")
		guild = await self.choose_guild(ctx)
		category = await sorting.get_last_category(guild, info)
		overwrites = { 
			guild.default_role: discord.PermissionOverwrite(send_messages = False),
			user: discord.PermissionOverwrite(manage_channels = True) 
		}
		
		await responses.confirm(ctx, f"A new channel will be created for {user.name}#{user.discriminator}.")
		
		channel = await guild.create_text_channel(user.name, category = category, overwrites = overwrites)
		await ctx.send(f":scroll: | {channel.mention} created for {user.mention}.")
	
	@commands.command(
		help = "Shows current Reddit feeds and allows deleting them.", 
		aliases = ("managefeed", "mf", "feeds")
	)	
	async def delfeed(self, ctx):
		guild = await self.choose_guild(ctx)
		query = await self.bot.dbc.execute("SELECT * FROM reddit_feeds WHERE guild = ?", (guild.id,))
		feeds = await query.fetchmany(size = self.MAX_FEEDS)
		
		values = []
		for feed in feeds:
			channel = getattr(await utils.get_channel(self.bot, feed[2]), "mention", "**invalid**")
			values.append(f"**r/{feed[3]}** to {channel} (query: *{feed[5]}*)")
			
		indice = await responses.choice(
			ctx,
			values,
			("\U0001F98A", "\U0001F428", "\U0001F42E"), 
			embeds.FEED, 
			"",
			f"Feeds for {guild.name}",
			"delete a feed"
		)
		await self.bot.dbc.execute("DELETE FROM reddit_feeds WHERE id = ?;", (feeds[indice][0],))
		
		await self.bot.dbc.commit()
		await ctx.send(":x: | Subreddit feed deleted.")
	
	@commands.command(
		help = "Displays a moderator message in a channel.\n By default, this is"
		" the channel the command is invoked in, but it can be specified beforehand.",
		aliases = ("m",)
	)
	async def modmessage(self, ctx, channel : typing.Optional[discord.TextChannel] = None, *, message_content):
		channel = channel or ctx.channel
		prompt = "This will be posted in this DM. To specify a channel, try again and mention it before your message."
		
		if isinstance(ctx.channel, discord.abc.GuildChannel): 
			prompt = f"This will be posted to {channel.mention} in **{channel.guild.name}**."
		
		await responses.confirm(ctx, prompt)
	
		embed = embeds.MOD_MESSAGE.create(message_content, "")
		embed.set_footer(
			text=f"Sent by {ctx.author.display_name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url=ctx.author.avatar_url_as(size=256)
		)

		await channel.send(embed=embed)
	
	@commands.guild_only()
	@commands.command(help = "Locks a channel, disabling the ability to send messages from it.", aliases = ("l",))	
	async def lock(self, ctx, channel : typing.Optional[discord.TextChannel] = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages = False)
		await ctx.send(f":lock: | **{ctx.channel.mention} has been locked.**")
		
	@commands.command(help = "Enables/disables non-essential commands for this server.", aliases = ("li",))	
	async def limit(self, ctx, enabled : bool):
		await self.set_flag(ctx, enabled, "limit_commands", ":stop_sign:", "Command limits have")
		
	@commands.command(help = "Enables/disables welcome and leave messages for a server.", aliases = ("wl", "welcome", "ms", "message"))	
	async def messages(self, ctx, enabled : bool):
		await self.set_flag(ctx, enabled, "welcome_users", ":envelope_with_arrow:", "Welcome and leave messages have")
	
	@commands.command(help = "Sets the leave message for this server.", aliases = ("sl", "setl"))	
	async def setleave(self, ctx):
		await self.set_message(ctx, True)
		
	@commands.command(help = "Sets the welcome message for this server.", aliases = ("sw", "setw"))	
	async def setwelcome(self, ctx):
		await self.set_message(ctx, False)
		
	@commands.command(help = "Enables/disables roll channel sorting for a server.", aliases = ("arrange", "s"))	
	async def sort(self, ctx, enabled : bool):
		await self.set_flag(ctx, enabled, "sort_channels", ":abcd:", "Roll channel sorting has")
	
	@commands.guild_only()	
	@commands.command(help = "Unlocks a channel, restoring the ability to send messages from it.",aliases=("ul",))	
	async def unlock(self, ctx, channel : discord.TextChannel = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages = True)
		await ctx.send(f":unlock: | **{ctx.channel.mention} has been unlocked.**")
		
	@staticmethod		
	async def choose_guild(ctx):
		if isinstance(ctx.channel, discord.abc.GuildChannel): return ctx.guild
		
		possible = []
		for guild in ctx.author.mutual_guilds:
			if await ctx.bot.is_owner(ctx.author):
				possible.append(guild)
				continue
			
			perms = guild.get_member(ctx.author.id).guild_permissions
			if perms.manage_guild or perms.administrator:
				possible.append(guild)
				
		if len(possible) == 1: 
			await ctx.send(f"Executing command in **{possible[0].name}**...")
			return possible[0]
				
		indice = await responses.choice(
			ctx,
			tuple(guild.name for guild in possible),
			("\U0001F3DB", "\U0001F3E2", "\U0001F3ED", "\U0001F3F0", "\U0001F3EF"), 
			embeds.CHOICE,
			"Multiple servers are available",
			None,
			"select a server to use the command in"
		) 
		
		return possible[indice]
	
	@staticmethod	
	async def set_flag(ctx, enabled, db_col, emoji, desc):
		guild = await ModerationTools.choose_guild(ctx)
		enabled_int = int(enabled)
		enabled_text = "enabled" if enabled else "disabled"
		 
		await ctx.bot.dbc.execute(f"UPDATE guilds SET {db_col} = ? WHERE discord_id = ?", (enabled_int, guild.id))
		await ctx.bot.dbc.commit()
		await ctx.send(f"{emoji} | {desc} been **{enabled_text}** for this server.")
		
		await ctx.bot.refresh_cache_guild(guild.id)
	
	@staticmethod	
	async def set_message(ctx, leave):
		guild = await ModerationTools.choose_guild(ctx)
		enabled = await ctx.bot.dbc.execute("SELECT welcome_users FROM guilds WHERE discord_id == ?;",(ctx.guild.id,))
		
		if enabled == 0: raise utils.CustomCommandError(
			"Welcome and leave messages disabled",
			"Your message cannot be set, as the welcome and leave message functionality"
			" is currently not operational. Turn it on with `!messages yes`."
		)
			
		result = await responses.respond_or_react(
			ctx,
			"Either type your message below, react with :leftwards_arrow_with_hook:"
			" to revert to the default, or with :x: to cancel.\n"
			"To include details, use `GUILD_NAME`, `MENTION`, or `MEMBER_NAME`.",
			["\U000021A9\U0000FE0F"]
		)
		
		if isinstance(result, discord.Message) or result[0].emoji == "\U000021A9\U0000FE0F":
			message_type = "welcome_text" if not leave else "leave_text"
			new = None if isinstance(result, tuple) else result.content
			
			await ctx.bot.dbc.execute(f"UPDATE guilds SET {message_type} = ? WHERE discord_id = ?;", (new, guild.id))
			await ctx.bot.dbc.commit()
			await ctx.send(":white_check_mark: | Message changed.")
		
def setup(bot):
	bot.add_cog(ModerationTools(bot))