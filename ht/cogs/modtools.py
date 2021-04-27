import discord, typing, asyncio
from discord.ext import commands
from datetime import datetime
from .. import utils

class ModerationTools(commands.Cog, name="Moderation"):
	def __init__(self, bot):
		self.bot = bot
		
	#right now, just a bodge of has_role, but expand this so it works in dm, by checking all valid servers under that circumstance
	async def cog_check(self,ctx):
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
		name="modmessage",
		help="Displays a moderator message in a channel.\n By default, this is"\
		" the channel the command is invoked in, but it can be specified beforehand.",
		aliases=("m",)
	)
	async def mod_message(self,ctx,channel : typing.Optional[discord.TextChannel] = None,*,message_content):
		channel = channel or ctx.channel
	
		embed = utils.nv_embed(message_content,"",kind=1)
		embed.set_footer(
			text=f"Sent by {ctx.author.display_name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url=ctx.author.avatar_url_as(size=256)
		)

		await channel.send(embed=embed)
	
	@commands.command(help="Locks a channel, disabling the ability to send messages from it.",aliases=("l",))	
	async def lock(self, ctx, channel : typing.Optional[discord.TextChannel] = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=False)
		await ctx.send(f":lock: | **{ctx.channel.mention} has been locked.**")
		
	@commands.command(help="Enables/disables welcome and leave messages for a server.",aliases=("wl","welcome","ms","message"))	
	async def messages(self, ctx, enabled : bool):
		enabled_int = int(enabled)
		enabled_text = "enabled" if enabled else "disabled"
		 
		await self.bot.dbc.execute("UPDATE guilds SET welcome_users = ? WHERE discord_id = ?",(enabled_int, ctx.guild.id))
		await self.bot.dbc.commit()
		await ctx.send(f":envelope_with_arrow: | Welcome and leave messages have been **{enabled_text}** for this server.")
	
	@commands.command(help="Sets the leave message for this server.",aliases=("sl","setl"))	
	async def setleave(self, ctx):
		await self.set_message(ctx, True)
		
	@commands.command(help="Sets the welcome message for this server.",aliases=("sw","setw"))	
	async def setwelcome(self, ctx):
		await self.set_message(ctx, False)
		
	@commands.command(help="Unlocks a channel, restoring the ability to send messages from it.",aliases=("ul",))	
	async def unlock(self, ctx, channel : discord.TextChannel = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=True)
		await ctx.send(f":unlock: | **{ctx.channel.mention} has been unlocked.**")
		
	@commands.command(help="Sends a warning message to a user.",aliases=("w",))	
	async def warn(self, ctx, user : discord.User, *, message_content):
		dm = await user.create_dm()
		
		if ctx.author == user:
			await ctx.send(utils.nv_embed(
				"Cannot warn oneself",
				"The warning could not be conducted, as warning oneself is prohibited."
			))
			return
		
		embed = utils.nv_embed(message_content,"",kind=1,custom_name="Moderator warning")
		embed.set_footer(
			text=f"From {ctx.guild.name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url=ctx.guild.icon_url_as(size=256)
		) #needs to be ascertained from dms once admin messages can be sent from there. 
		
		await ctx.send("Warning sent.")
		await dm.send(embed=embed)
		
	async def set_message(self, ctx, leave):
		enabled = await self.bot.dbc.execute("SELECT welcome_users FROM guilds WHERE discord_id == ?;",(ctx.guild.id,))
		
		if enabled == 0:
			await ctx.send(utils.nv_embed(
				"Welcome and leave messages disabled",
				"Your message cannot be set, as the welcome and leave message functionality"\
				" is currently not operational. Turn it on with `!messages yes`."
			))
			return
			
		reactions = ("\U0000274C","\U000021A9")
		
		def check_react(reaction, user):
			if ctx.author != user: return False
			return reaction.message == message and reaction.emoji in reactions 
		
		def check_message(message):
			return ctx.author == message.author 
		
		message = await ctx.send(
			"Either type your message below, react with :leftwards_arrow_with_hook:"\
			" to revert to the default, or with :x: to cancel.\n"\
			"To include details, use `GUILD_NAME`, `MENTION`, or `MEMBER_NAME`."
		)
		await asyncio.gather(*[message.add_reaction(r) for r in reactions])
		
		done, pending = await asyncio.wait(
			[self.bot.wait_for("reaction_add", check = check_react, timeout = 360),
			 self.bot.wait_for("message", check = check_message, timeout = 360)], 
			return_when = asyncio.FIRST_COMPLETED
		)
		
		try:
			result = done.pop().result()
		except asyncio.TimeoutError:
			await ctx.send(":x: | Command timed out.")
			return
			
		for future in pending: future.cancel()	#ignore anything else
		for future in done: future.exception() #retrieve and ignore any other completed future's exception
		
		if isinstance(result, tuple) and result[0].emoji == reactions[0]:
			await ctx.send(":x: | Command cancelled.")
			
		elif isinstance(result, discord.Message) or result[0].emoji == reactions[1]:
			message_type = "welcome_text" if not leave else "leave_text"
			new = None if isinstance(result, tuple) else result.content
			
			await self.bot.dbc.execute(f"UPDATE guilds SET {message_type} = ? WHERE discord_id = ?;",(new, ctx.guild.id))
			await self.bot.dbc.commit()
			await ctx.send(":white_check_mark: | Command changed.")
		
def setup(bot):
	bot.add_cog(ModerationTools(bot))