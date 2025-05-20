import discord, aiohttp, asyncio, functools, json, io
from discord import app_commands
from discord.ext import commands
from logging import Formatter
from textwrap import TextWrapper
from datetime import timedelta
from dateutil.tz import gettz
from . import __version__, views

class MeldedCog(commands.Cog):
	def __init_subclass__(self, *args, **kwargs):
		super().__init_subclass__()
		self.category = kwargs.pop("category", self.__cog_name__)
		self.limit = kwargs.pop("limit", True)

		async def cog_check(self, ctx):
			return await check_limited(ctx)

		if self.limit:
			self.cog_check = cog_check

		return self

class ModCog(MeldedCog, limit = False):
	def __init_subclass__(self, *args, **kwargs):
		super().__init_subclass__(category = "Moderation", limit = False)

	async def cog_load(self):
		for command in self.get_commands():
			if type(command) != commands.HybridCommand: continue
			command.app_command.default_permissions = discord.Permissions(ban_members = True)

	async def cog_check(self, ctx):
		if await ctx.bot.is_owner(ctx.author):
			return True
		elif isinstance(ctx.channel, discord.abc.GuildChannel):
			if is_mod(ctx.author):
				return True
		else:
			for guild in ctx.author.mutual_guilds:
				perms = guild.get_member(ctx.author.id)
				if is_mod(perms): return True

		raise commands.MissingRole("admin")

class NvFormatter(Formatter):
	LINE_WIDTH = 100
	wrapper = TextWrapper(width = LINE_WIDTH)

	def __init__(self):
		super().__init__()

	def format(self, record):
		message = record.getMessage()
		
		if record.exc_info:
			if not record.exc_text:
				record.exc_text = self.formatException(record.exc_info)
		
		if record.exc_text:
			message += "\n" + record.exc_text

		if "\n" not in message[:self.LINE_WIDTH + 80]:
			lines = self.wrapper.wrap(message)
		else:
			lines = message.splitlines()

		message = f"\n{' ' * 7} | {' ' * 17} | ".join(lines)
		return f"{record.levelname:7} | {record.name:17} | {message}"

class BadMessageResponse(Exception):
	pass

class CommandCancelled(commands.CommandError, app_commands.AppCommandError):
	pass

class CustomCommandError(commands.CommandError, app_commands.AppCommandError):
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

async def post_json(session, url, data, **kwargs):
	async with session.post(url, json=data, headers={"Accept": "application/json"}) as source:
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
	
async def check_is_owner(ctx):
	if not await ctx.bot.is_owner(ctx.author):
		raise commands.NotOwner("Owner-only mode is enabled")
		return False
	return True

async def check_limited(ctx):
	if not ctx.guild: return True

	if ctx.bot.guild_cache[ctx.guild.id][1]["limit_commands"]:
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
	
def get_special_channel(bot, channel):
	channel = bot.channel_cache.get(channel.id)
	
	if channel and (channel["oc"] or channel["proposals"]):
		return channel
		
	return None
	
def is_mod(member):
	perms = getattr(member, "guild_permissions", None)
	if not perms: return True
	
	return perms.ban_members or perms.administrator

async def _typing(self, ctx):
	await ctx.typing()

trigger_typing = commands.before_invoke(_typing)
