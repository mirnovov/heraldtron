import discord, typing, asyncio
from discord.ext import commands
from datetime import datetime
from .. import utils

class ModerationTools(commands.Cog, name = "Moderation"):
	def __init__(self, bot):
		self.bot = bot
		
	#right now, just a bodge of has_role, but expand this so it works in dm, by checking all valid servers under that circumstance
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
		
	@commands.command(help = "Sets the welcome message for this server.",aliases = ("sw", "setw"))	
	async def setwelcome(self, ctx):
		await self.set_message(ctx, False)
		
	@commands.command(help = "Unlocks a channel, restoring the ability to send messages from it.",aliases=("ul",))	
	async def unlock(self, ctx, channel : discord.TextChannel = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=True)
		await ctx.send(f":unlock: | **{ctx.channel.mention} has been unlocked.**")
		
	async def set_message(self, ctx, leave):
		enabled = await self.bot.dbc.execute("SELECT welcome_users FROM guilds WHERE discord_id == ?;",(ctx.guild.id,))
		
		if enabled == 0:
			await ctx.send(embeds.ERROR.create(
				"Welcome and leave messages disabled",
				"Your message cannot be set, as the welcome and leave message functionality"\
				" is currently not operational. Turn it on with `!messages yes`."
			))
			return
			
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