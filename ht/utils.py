import discord
from discord.ext import commands

def nv_error(error_summary,error_description):
	embed=discord.Embed(title=error_summary,description=error_description, color=0xdd3333)
	embed.set_author(
		name="An error has been encountered",
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/OOjs_UI_icon_error-destructive.svg/"\
		"200px-OOjs_UI_icon_error-destructive.svg.png"
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