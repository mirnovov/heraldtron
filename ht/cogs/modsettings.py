import discord, asyncio, typing, re
from discord import ui
from discord.ext import commands
from .. import converters, embeds, utils, views

class ModerationSettings(utils.ModCog, name = "Settings"):
	MAX_FEEDS = 3
	SR_VAL = re.compile("(r\/|\/|r\/)+")
	
	def __init__(self, bot):
		self.bot = bot
			
	@commands.command(help = "Sets up a channel for proposals.", aliases = ("ap", "proposals"))	
	async def addproposals(self, ctx, channel : discord.TextChannel):
		await self.set_channel(ctx, channel, "proposal", False, "proposals")
		
	@commands.command(help = "Sets up a channel for OC.", aliases = ("ao", "oc"))	
	async def addoc(self, ctx, channel : discord.TextChannel):
		await self.set_channel(ctx, channel, "oc", False, "OC")
		
	@commands.command(help = "Disables proposal functionality in a channel.", aliases = ("dp",))	
	async def delproposals(self, ctx, channel : discord.TextChannel):
		await self.set_channel(ctx, channel, "proposal", True, "proposals")
		
	@commands.command(help = "Disables OC functionality in a channel.", aliases = ("do",))	
	async def deloc(self, ctx, channel : discord.TextChannel):
		await self.set_channel(ctx, channel, "oc", True, "OC")
	
	@commands.command(name = "limit", help = "Enables/disables non-essential commands for this server.", aliases = ("li",))	
	async def limitmessages(self, ctx, enabled : bool):
		await self.set_flag(ctx, enabled, "limit_commands", ":stop_sign:", "Command limits have")
		
	@commands.command(help = "Enables/disables welcome and leave messages for a server.", aliases = ("wl", "welcome", "ms", "message"))	
	async def messages(self, ctx, enabled : bool):
		await self.set_flag(ctx, enabled, "welcome_users", ":envelope_with_arrow:", "Welcome and leave messages have")
		
	@commands.command(help = "Enables/disables roll functionality for this server.", aliases = ("rl",))	
	async def rollserver(self, ctx, enabled : bool):
		await self.set_flag(ctx, enabled, "roll", ":scroll:", "Roll functionaliy has")
	
	@commands.command(help = "Sets the leave message for this server.", aliases = ("sl", "setl"))	
	async def setleave(self, ctx):
		await self.set_message(ctx, True)
		
	@commands.command(help = "Sets the welcome message for this server.", aliases = ("sw", "setw"))	
	async def setwelcome(self, ctx):
		await self.set_message(ctx, False)
		
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
		
		choices = tuple(discord.SelectOption(label = a.name) for a in possible)
		indice = await views.Chooser(ctx, choices, "Execute").run(
			"**Multiple servers are available.** Select a server to use the command in:", 
		)		
		return possible[indice]
		
	async def set_channel(self, ctx, channel, column, remove, purpose):
		guild = await self.choose_guild(ctx)
		value = int(not remove)
		
		await self.bot.dbc.execute(
			f"INSERT INTO channels (discord_id, guild, {column}) VALUES " +
			f"(?, ?, ?) ON CONFLICT(discord_id) DO UPDATE SET {column} = ?;",
			(channel.id, guild.id, value, column)
		)
		await ctx.bot.dbc.commit()
		
		if guild != channel.guild:
			raise utils.CustomCommandError(
				"Incorrect server", "The channel specified does not belong to this server."
			)
		
		self.bot.channel_cache[channel.id] = await self.bot.dbc.execute_fetchone(
			"SELECT * FROM channels WHERE discord_id = ?;", (channel.id,)
		)
		
		await ctx.send(
			f":white_check_mark: | {channel.mention} set up for {purpose}." 
			if not remove else 
			f":x: | Functionality for {purpose} removed from {channel.mention}."
		)
	
	@staticmethod	
	async def set_flag(ctx, enabled, db_col, emoji, desc):
		guild = await ModerationSettings.choose_guild(ctx)
		enabled_int = int(enabled)
		enabled_text = "enabled" if enabled else "disabled"
		 
		await ctx.bot.dbc.execute(f"UPDATE guilds SET {db_col} = ? WHERE discord_id = ?", (enabled_int, guild.id))
		await ctx.bot.dbc.commit()
		await ctx.send(f"{emoji} | {desc} been **{enabled_text}** for this server.")
		
		await ctx.bot.refresh_cache_guild(guild.id)
	
	@staticmethod	
	async def set_message(ctx, leave):
		guild = await ModerationSettings.choose_guild(ctx)
		enabled = await ctx.bot.dbc.execute("SELECT welcome_users FROM guilds WHERE discord_id == ?;", (guild.id,))
		
		if enabled == 0: raise utils.CustomCommandError(
			"Welcome and leave messages disabled",
			"Your message cannot be set, as the welcome and leave message functionality"
			f" is currently not operational. Turn it on with `{ctx.clean_prefix}messages yes`."
		)
		
		reset = ui.Button(label = "Reset to default", style = discord.ButtonStyle.secondary)	
		result = await views.RespondOrReact(ctx, additional = (reset,)).run(
			"Type your message below. To add details, include `GUILD_NAME`,"
			" `MENTION`, or `MEMBER_NAME` in the message.",
		)
		
		if result == "Reset to default" or isinstance(result, discord.Message):
			message_type = "welcome_text" if not leave else "leave_text"
			new = None if isinstance(result, str) else result.content
			
			await ctx.bot.dbc.execute(f"UPDATE guilds SET {message_type} = ? WHERE discord_id = ?;", (new, guild.id))
			await ctx.bot.dbc.commit()
			await ctx.send(":white_check_mark: | Message changed.")
		
def setup(bot):
	bot.add_cog(ModerationSettings(bot))
