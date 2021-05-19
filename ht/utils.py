import discord, aiohttp, asyncio, functools, json, io
from discord.ext import commands
from logging import Formatter
from textwrap import TextWrapper
from xml.etree import ElementTree
from . import __version__

class NvFormatter(Formatter):
	LINE_WIDTH = 100
	wrapper = TextWrapper(width = LINE_WIDTH)
	
	def __init__(self):
		super().__init__()
	
	def format(self, record):
		message = record.getMessage()
		
		if "\n" not in message[:self.LINE_WIDTH + 80]:
			lines = self.wrapper.wrap(message)
		else:
			lines = message.splitlines()
			
		message = f"\n{' ' * 7} | {' ' * 15} | ".join(lines)
		return f"{record.levelname:7} | {record.name:15} | {message}"
	
class BadMessageResponse(Exception):
	pass
		
class CommandCancelled(commands.CommandError):
	@classmethod
	async def create(self, message, ctx):
		await ctx.send(f":x: | {message}.")
		return CommandCancelled(message)
		
class CustomCommandError(commands.CommandError):
	def __init__(self, title, desc, *args, **kwargs):
		self.title = title
		self.desc = desc
		
USER_AGENT = f"{aiohttp.http.SERVER_SOFTWARE} Heraldtron/{__version__} (like Herald 3.0)" #for fun
	
async def get_bytes(session, url, **kwargs):
	async with session.get(url) as source:
		image = await source.read(**kwargs)
		return io.BytesIO(image)
	
async def get_json(session, url, **kwargs):
	async with session.get(url) as source:
		return await source.json(**kwargs)
			
async def get_text(session, url, **kwargs):
	async with session.get(url) as source:
		return await source.text(**kwargs)	
		
async def get_channel(bot, channel):
	return bot.get_channel(channel) or await bot.fetch_channel(channel)
	
async def get_guild(bot, guild):
	return bot.get_guild(guild) or await bot.fetch_guild(guild)
	
async def get_user(bot, user):
	return bot.get_user(user) or await bot.fetch_user(user)
	
async def fetchone(dbc, query, substs = None):
	cursor = await dbc.execute(query, substs)
	return await cursor.fetchone()
	
async def unqualify_name(bot, name, discriminator):
	return discord.utils.find(
		lambda m: m.name == name and m.discriminator == discriminator, bot.users
	)
	
async def check_is_owner(ctx):
	if not await ctx.bot.is_owner(ctx.author):
		raise commands.NotOwner("Owner-only mode is enabled")
		return False
	return True
	
async def check_limited(ctx):
	if not ctx.guild: return True
		
	limited = await fetchone(
		ctx.bot.dbc,
		"SELECT limit_commands FROM guilds WHERE discord_id = ?",
		(ctx.guild.id,)
	)
	
	if limited[0] == 1: 
		raise CustomCommandError(
			"Command prohibited",
			"This command is not allowed on this server."
		)
		return False
	
	return True
	
def parse_xml(text_string, root):
	return ElementTree.fromstring(text_string).find(root)

@functools.cache	
def pronounise(word):
	pron = "an" if word.strip()[0].upper() in "AEIOU1" else "a"
	return f"{pron} {word}"
	
@functools.cache
def stdtime(value):
	return f"{value.day} {value:%B} {value.year}"

async def _typing(self, ctx): 
	await ctx.trigger_typing()
	
trigger_typing = commands.before_invoke(_typing)