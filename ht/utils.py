import discord, aiohttp, asyncio, functools, json, io
from discord.ext import commands
from logging import Formatter
from textwrap import TextWrapper
from datetime import timedelta
from dateutil.tz import gettz
from . import __version__

class MeldedCog(commands.Cog):
	def __init_subclass__(self, *args, **kwargs):
		super().__init_subclass__()
		self.category = kwargs.pop("category", None)
		self.limit = kwargs.pop("limit", True)
		
		async def cog_check(self, ctx):
			return await check_limited(ctx)
			
		if self.limit:
			self.cog_check = cog_check
		
		return self

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
	
	if ctx.bot.guild_cache[ctx.guild.id][1][2]: 
		raise CustomCommandError(
			"Command prohibited",
			"This command is not allowed on this server."
		)
		return False
	
	return True

@functools.cache	
def pronounise(word):
	pron = "an" if word.strip()[0].upper() in "AEIOU1" else "a"
	return f"{pron} {word}"
	
@functools.cache
def pluralise(word, count):
	amended = word if count == 1 else f"{word}s"
	return f"{count} {amended}"
	
@functools.cache
def stddate(value):
	return f"{value.day} {value:%B} {value.year}"
	
@functools.cache
def stddatetime(value, timezone = None):
	if timezone:
		value = value.astimezone(gettz(timezone))
		tzsuffix = timezone.split("/")[-1].replace("_"," ")
	else: 
		tzsuffix = value.tzname()
		
	if value.utcoffset():
		tzsuffix += f" (+{value.utcoffset().seconds // 60 / 60:g})"
	
	time = value.strftime("%I:%M %p").lower()
	return f"{time} {value.day} {value:%B} {value.year} {tzsuffix}"
	
@functools.cache
def stddelta(value):
	if value.total_seconds() < 0:
		inverse = -value + timedelta(minutes = 1)
		return f"-{stddelta(inverse)}"
	
	minutes = value.seconds // 60
	hours = minutes // 60
	days = value.days
	
	if days != 0 and hours != 0:
		return f"{pluralise('day', days)}, {pluralise('hour', hours)}"
	elif days != 0:
		return pluralise("day", days)
	elif hours != 0:
		return pluralise("hour", hours)
	else:
		return pluralise("minute", minutes)	

async def _typing(self, ctx): 
	await ctx.trigger_typing()
	
trigger_typing = commands.before_invoke(_typing)