import discord, urllib.request, json, functools
from discord.ext import commands

@functools.cache
def nv_embed(e_summary,e_description,kind=0,custom_name=None):
	embed=discord.Embed(title=e_summary,description=e_description)
	
	#0, default, error
	color = 0xdd3333
	name = "An error has been encountered"
	icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/OOjs_UI_icon_error-destructive.svg/"\
	"200px-OOjs_UI_icon_error-destructive.svg.png"
	
	if kind == 1: #mod warning
		color = 0xff5d01
		name = "Official moderator message"
		icon_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/OOjs_UI_icon_notice-warning.svg/"\
		"240px-OOjs_UI_icon_notice-warning.svg.png"
	elif kind == 2: #help
		color = 0x3365ca
		name = "Command help"
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/OOjs_UI_icon_info-progressive.svg/"\
		"240px-OOjs_UI_icon_info-progressive.svg.png"
	elif kind == 3: #search
		color=0xfafafa
		name="Lookup results" 
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/OOjs_UI_icon_search-ltr-invert.svg/"\
		"240px-OOjs_UI_icon_search-ltr-invert.svg.png"
	elif kind == 4: #generic
		color=0xfafafa
		name="Results" 
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/VisualEditor_icon_reference-rtl-invert.svg/"\
		"240px-VisualEditor_icon_reference-invert.svg.png"
		
	embed.color=color
	embed.set_author(name=custom_name or name,icon_url=icon_url)
	
	return embed

#right now, just a duplicate of has_role, but expand this so it works in dm, by checking all valid servers under that circumstance
@functools.cache
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
	
def get_json(url):
	with urllib.request.urlopen(url) as url:
		return json.loads(url.read().decode())
	return None