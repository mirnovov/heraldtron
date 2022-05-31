import discord, typing, re
from discord.ext import commands
from datetime import datetime
from .. import embeds, utils, views

class ModerationTools(utils.ModCog, name = "Tools"):
	HAS_MARKDOWN = re.compile(r"<@!?|<#|<&|\*{1,2}\w")
	SHORT_MESSAGE = 200

	def __init__(self, bot):
		self.bot = bot

	@commands.command(
		help = "Displays a moderator message in a channel.\n By default, this is"
		" the channel the command is invoked in, but it can be specified beforehand.",
		aliases = ("m",)
	)
	async def modmessage(self, ctx, channel : typing.Optional[discord.TextChannel] = None, *, message_content):
		channel = channel or ctx.channel
		prompt = f"Send a message to this DM? To specify a channel, try again and mention it before your message."

		if isinstance(ctx.channel, discord.abc.GuildChannel):
			prompt = f"Send a message in {channel.mention} of **{channel.guild.name}**?"

		await views.Confirm(ctx, "Create", delete = True).run(prompt)

		if len(message_content) < self.SHORT_MESSAGE and not re.search(self.HAS_MARKDOWN, message_content):
			embed = embeds.MOD_MESSAGE.create(message_content, "")
		else:
			embed = embeds.MOD_MESSAGE.create("", message_content)

		embed.set_footer(
			text = f"Sent by {ctx.author.display_name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url = ctx.author.display_avatar.with_size(256).url
		)

		await channel.send(embed = embed)

	@commands.guild_only()
	@commands.command(help = "Locks a channel, disabling the ability to send messages from it.", aliases = ("l",))
	async def lock(self, ctx, channel : typing.Optional[discord.TextChannel] = None):
		channel = channel or ctx.channel

		overwrite = discord.PermissionOverwrite(send_messages = False)
		await channel.set_permissions(ctx.guild.default_role, overwrite = overwrite)
		await ctx.send(f":lock: | **{ctx.channel.mention} has been locked.**")

	@commands.guild_only()
	@commands.command(help = "Unlocks a channel, restoring the ability to send messages from it.",aliases=("ul",))
	async def unlock(self, ctx, channel : discord.TextChannel = None):
		channel = channel or ctx.channel

		overwrite = discord.PermissionOverwrite(send_messages = True)
		await channel.set_permissions(ctx.guild.default_role, overwrite = overwrite)
		await ctx.send(f":unlock: | **{ctx.channel.mention} has been unlocked.**")

def setup(bot):
	bot.add_cog(ModerationTools(bot))
