import discord, aiohttp, asyncio, json, functools, urllib, os
from discord.ext import commands
from io import BytesIO
from xml.etree import ElementTree

def nv_embed(e_summary,e_description,kind=0,custom_name=None,custom_icon=None):
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
		color=0x444850
		name="Lookup results" 
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/OOjs_UI_icon_search-ltr-invert.svg/"\
		"240px-OOjs_UI_icon_search-ltr-invert.svg.png"
	elif kind == 4: #generic
		color=0x444850
		name="Results" 
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/VisualEditor_icon_reference-rtl-invert.svg/"\
		"240px-VisualEditor_icon_reference-invert.svg.png"
	elif kind == 5: #about
		color=0x02af89
		name="About Heraldtron" 
		icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Echo_gratitude.svg/"\
		"240px-Echo_gratitude.svg.png"
		
	embed.color=color
	embed.set_author(name=custom_name or name,icon_url=custom_icon or icon_url)
	
	return embed
	
async def typing(self, ctx):
	await ctx.trigger_typing()
	
async def get_bytes(session, url):
	async with session.get(url) as source:
		if not source.ok: return None
		try:
			image = await source.read()
		except aiohttp.ClientResponseError:
			return None
		return BytesIO(image)
	
async def get_json(session, url, **kwargs):
	async with session.get(url) as source:
		if not source.ok: return None
		return await source.json(**kwargs)
			
async def get_text(session, url):
	async with session.get(url) as source:
		if not source.ok: return None
		return await source.text()	
			
async def get_guild_row(bot, guild_id):
	cursor = await bot.dbc.execute("SELECT * FROM guilds WHERE discord_id == ?;",(guild_id,))
	return await cursor.fetchone()
			
def parse_xml(text_string, root):
	return ElementTree.fromstring(text_string).find(root)
	
def qualify_name(member):
	return f"{member.name}#{member.discriminator}"
	
async def check_is_owner(ctx):
	if not await ctx.bot.is_owner(ctx.author):
		raise commands.NotOwner("Owner-only mode is enabled")
		return False
	return True
	
async def respond_or_react(ctx, message, reactions, timeout = 360, requires_image = False):
	def check_react(reaction, user):
		if ctx.author != user: return False
		return reaction.message == message and reaction.emoji in reactions 
	
	def check_message(message):
		if ctx.author != message.author:
			return False
		elif requires_image:
			is_image = message.attachments[0].content_type.startswith("image")
			return len(message.attachments) > 0 and is_image
		return True
	
	message = await ctx.send(message)
	await add_multiple_reactions(message, reactions)
	
	done, pending = await asyncio.wait(
		[ctx.bot.wait_for("reaction_add", check = check_react, timeout = timeout),
		 ctx.bot.wait_for("message", check = check_message, timeout = timeout)], 
		return_when = asyncio.FIRST_COMPLETED
	)
	
	try:
		result = done.pop().result()
	except asyncio.TimeoutError:
		await ctx.send(":x: | Command timed out.")
		return None
		
	for future in pending: future.cancel()	#ignore anything else
	for future in done: future.exception() #retrieve and ignore any other completed future's exception
	
	return result
	
async def add_multiple_reactions(message, reactions):
	return await asyncio.gather(*[message.add_reaction(r) for r in reactions])
