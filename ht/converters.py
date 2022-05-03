import warnings, csv, re, sys
from discord.ext import commands
from datetime import timezone
from dateutil import parser as duparser
from . import utils

class Armiger(commands.Converter):
	async def convert(self, ctx, argument):
		result = None
		
		if argument.isdecimal():
			result = await ctx.bot.dbc.execute_fetchone(
				"SELECT * FROM armigers_e WHERE greii_n == ?;",
				(int(argument),)
			)
		elif argument.startswith("<"):
			try:
				member = await commands.MemberConverter().convert(ctx, argument)
				result = await ctx.bot.dbc.execute_fetchone(
					"SELECT * FROM armigers_e WHERE discord_id == ?;",
					(member.id,)
				)
			except commands.MemberNotFound: pass
		elif "#" in argument:
			parts = argument.split("#")
			result = await ctx.bot.dbc.execute_fetchone(
				"SELECT * FROM armigers_e WHERE qualified_name LIKE ?1 AND qualified_id == ?2;",
				(parts[0], parts[1])
			)
		else:
			result = await ctx.bot.dbc.execute_fetchone(
				"SELECT * FROM armigers_e WHERE qualified_name LIKE ?;",
				(f"%{argument}%",)
			)
			
		if result: return result
		raise utils.CustomCommandError(
			"Invalid armiger",
			"The armiger you entered does not exist. Check that you spelled their name correctly."
		)
		
class Range(commands.Converter):
	def __init__(self, min, max):
		self.min = min
		self.max = max
		self.range = range(min, max)
		
	async def convert(self, ctx, argument):
		try:
			argument = int(argument)
		except ValueError:
			raise commands.BadArgument("Argument must be integer")
		
		if argument not in self.range:
			raise utils.CustomCommandError(
				"Number not in range",
				f"The number you entered must be between {self.min} and {self.max}."
			)
		return argument
		
class Url(commands.Converter):
	VALID = re.compile(r"\S+\.\S{1,4}\S*")
	
	async def convert(self, ctx, argument):
		if re.match(Url.VALID, argument):
			return argument
		else:
			raise utils.CustomCommandError(
				"Invalid URL",
				f"The URL entered is not in the correct format."
			)
			
class MemberOrUser(commands.Converter):
	async def convert(self, ctx, argument):
		try:
			return await commands.MemberConverter().convert(ctx, argument)
		except commands.MemberNotFound: pass
		
		try:
			return await commands.UserConverter().convert(ctx, argument)
		except commands.UserNotFound: pass
		
		#use the armigers db as a basis for partial matching,
		#since discord.py only does whole matches (and it would be too
		#inefficient to redo its behaviour with that)
		query = await ctx.bot.dbc.execute_fetchone(
			"SELECT * FROM armigers_e WHERE qualified_name LIKE ? AND discord_id IS NOT NULL",
			(f"%{argument}%",)
		)
		if query:
			user = await utils.get_user(ctx.bot, query[1]) 
			if user: return user
		
		raise commands.UserNotFound(argument)
		
class RollVariant(commands.Converter):
	async def convert(self, ctx, argument):
		variants = ctx.bot.get_cog("Roll Sorting").VARIANTS
		
		try:
			argument = int(argument)
			return (*variants[argument], False)
		except ValueError: pass
		
		kw = tuple(v[1] for v in variants)
		
		if argument in kw:
			return (*variants[kw.index(argument)], False)
		
		raise utils.CustomCommandError(
			"Invalid roll variant",
			"The item you entered is not a valid roll channel type."
		)
		
class Date(commands.Converter):
	def __init__(self):
		warnings.simplefilter("error", duparser.UnknownTimezoneWarning)
		
		if not getattr(Date, "timezones", 0):
			#only do this once, and save it for all class members
			with open("data/tz.csv") as file:
				csvdata = {a: int(b) for (a, b) in csv.reader(file, delimiter = ";")}
			
			setattr(Date, "timezones", csvdata)
	
	async def convert(self, ctx, argument):	
		try:	
			date = duparser.parse(argument, fuzzy = True, tzinfos = self.timezones)
		except ValueError:
			raise utils.CustomCommandError(
				"Invalid date",
				"The date you entered is in an unrecognisable format."
			)
		except duparser.UnknownTimezoneWarning:	
			raise utils.CustomCommandError(
				"Invalid timezone",
				"The timezone you entered is invalid."
			)			
		
		return date.astimezone(timezone.utc)
