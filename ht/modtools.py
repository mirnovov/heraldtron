import discord, typing
from discord.ext import commands
from datetime import datetime
from . import utils

class ModerationTools(commands.Cog, name="Moderation"):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(
		name="modmessage",
		help="Displays a moderator message in a certain channel specified beforehand.",
		aliases=("m",)
	)
	@utils.is_admin()
	async def mod_message(self,ctx,channel : typing.Optional[discord.TextChannel] = None,*,message_content):
		channel = channel or ctx.channel
	
		embed=discord.Embed(title=message_content, color=0xff5d01)
		embed.set_author(
			name="Official moderator message",
			icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/OOjs_UI_icon_notice-warning.svg/"\
			"240px-OOjs_UI_icon_notice-warning.svg.png"
		)
		embed.set_footer(
			text=f"Sent by {ctx.author.display_name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url=ctx.author.avatar_url_as(size=256)
		)

		await channel.send(embed=embed)
	
	@commands.command(help="Locks a channel, disabling the ability to send messages from it.",aliases=("l",))	
	@utils.is_admin()
	async def lock(self, ctx, channel : typing.Optional[discord.TextChannel] = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=False)
		await ctx.send(f":lock: | **{ctx.channel.mention} has been locked.**")
		
	@commands.command(help="Unlocks a channel, restoring the ability to send messages from it.",aliases=("ul",))	
	@utils.is_admin()
	async def unlock(self, ctx, channel : discord.TextChannel = None):
		channel = channel or ctx.channel
		
		await channel.set_permissions(ctx.guild.default_role, send_messages=True)
		await ctx.send(f":unlock: | **{ctx.channel.mention} has been unlocked.**")
		
		
def setup(bot):
	bot.add_cog(ModerationTools(bot))