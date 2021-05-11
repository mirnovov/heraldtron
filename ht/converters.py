from discord.ext import commands
from . import utils

class Armiger(commands.Converter):
	async def convert(self, ctx, argument):
		if not argument:
			#actually still *is* an argument. Fuck you, Stefan Molyneux
			argument = ctx.member.name
		
		result = None
		
		if argument.isdecimal():
			result = await utils.fetchone(
				ctx.bot.dbc, 
				"SELECT * FROM armigers WHERE greii_n == ?;",
				(int(argument),)
			)
		elif argument.startswith("<"):
			try:
				member = await commands.MemberConverter().convert(ctx, argument)
				result = await utils.fetchone(
					ctx.bot.dbc, 
					"SELECT * FROM armigers WHERE discord_id == ?;",
					(member.id,)
				)
			except commands.MemberNotFound: pass
		elif "#" in argument:
			parts = argument.split("#")
			result = await utils.fetchone(
				ctx.bot.dbc, 
				"SELECT * FROM armigers WHERE qualified_name LIKE ? AND qualified_id == ?;",
				(parts[0], parts[1])
			)
		else:
			result = await utils.fetchone(
				ctx.bot.dbc, 
				"SELECT * FROM armigers WHERE qualified_name LIKE ?",
				(f"%{argument}%",)
			)
			
		if result: return result
		raise commands.BadArgument("Invalid argument")
		
#add general-purpose advanced member (allow https://discordpy.readthedocs.io/en/latest/api.html#discord.Guild.query_members) and channel converters