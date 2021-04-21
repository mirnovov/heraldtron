import discord, aiohttp, json, functools, urllib, os
from discord.ext import commands
from io import BytesIO
from xml.etree import ElementTree
from .ext import get_slow_client_session

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
	
async def typing(self,ctx):
	await ctx.trigger_typing()
	
async def get_bytes(url):
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as source:
			if not source.ok: return None
			try:
				image = await source.read()
			except aiohttp.ClientResponseError:
				return None
			return BytesIO(image)
	
async def get_json(url, slow_mode = False):
	cs = aiohttp.ClientSession() if not slow_mode else get_slow_client_session() 
	
	async with cs as session:
		async with session.get(url) as source:
			if not source.ok: return None
			return await source.json()
			
async def get_text(url):
	async with aiohttp.ClientSession()  as session:
		async with session.get(url) as source:
			if not source.ok: return None
			return await source.text()	
			
def parse_xml(text_string,root):
	return ElementTree.fromstring(text_string).find(root)
	
def load_conf():
	with open("config.json") as file:
		try: conf = json.load(file)
		except: raise FileNotFoundError("Cannot load JSON file.")
		
	requisites = [
		"DISCORD_TOKEN", "GCS_TOKEN", "GCS_CX", "AR_RIJKS", 
		"AR_EURO", "AR_DGTNZ", "AR_SMTHS", "AR_DDBTK", "DEEP_AI"
	]
	
	for r in requisites:
		if r not in conf:
			raise NameError("JSON file does not have required values.")
			
	return conf
