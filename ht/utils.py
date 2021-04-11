import discord
from discord.ext import commands

def nv_embed(e_summary,e_description,kind=0):
	embed=discord.Embed(title=e_summary,description=e_description)
	
	if kind == 0: #error
		embed.color = 0xdd3333
		embed.set_author(
			name="An error has been encountered",
			icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/OOjs_UI_icon_error-destructive.svg/"\
			"200px-OOjs_UI_icon_error-destructive.svg.png"
		)
	elif kind == 1: #mod warning
		embed.color=0xff5d01
		embed.set_author(
			name="Official moderator message",
			icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/OOjs_UI_icon_notice-warning.svg/"\
			"240px-OOjs_UI_icon_notice-warning.svg.png"
		)
	elif kind == 2: #help
		embed.color=0x3365ca
		embed.set_author(
			name="Command help",
			icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/OOjs_UI_icon_info-progressive.svg/"\
			"240px-OOjs_UI_icon_info-progressive.svg.png"
		)
	
	return embed

#right now, just a duplicate of has_role, but expand this so it works in dm, by checking all valid servers under that circumstance
def is_admin(item="Herald"):
	def predicate(ctx):
		if not isinstance(ctx.channel, discord.abc.GuildChannel):
			raise commands.NoPrivateMessage()

		if isinstance(item, int):
			role = discord.utils.get(ctx.author.roles, id=item)
		else:
			role = discord.utils.get(ctx.author.roles, name=item)
		if role is None:
			raise commands.MissingRole(item)
		return True

	return commands.core.check(predicate)