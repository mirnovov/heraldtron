import discord, aiohttp, asyncio, json
from discord.ext import commands
from io import BytesIO
from xml.etree import ElementTree

async def typing(self, ctx):
	await ctx.trigger_typing()
	
async def get_bytes(session, url, **kwargs):
	async with session.get(url) as source:
		image = await source.read(**kwargs)
		return BytesIO(image)
	
async def get_json(session, url, **kwargs):
	async with session.get(url) as source:
		return await source.json(**kwargs)
			
async def get_text(session, url, **kwargs):
	async with session.get(url) as source:
		return await source.text(**kwargs)	
			
async def get_guild_row(bot, guild_id):
	cursor = await bot.dbc.execute("SELECT * FROM guilds WHERE discord_id == ?;",(guild_id,))
	return await cursor.fetchone()
			
def parse_xml(text_string, root):
	return ElementTree.fromstring(text_string).find(root)
	
def qualify_name(member):
	return f"{member.name}#{member.discriminator}"
	
def pronounise(word):
	pron = "an" if word.strip()[0].upper() in "AEIOU1" else "a"
	return f"{pron} {word}"
	
async def check_is_owner(ctx):
	if not await ctx.bot.is_owner(ctx.author):
		raise commands.NotOwner("Owner-only mode is enabled")
		return False
	return True
	
async def respond_or_react(ctx, message, reactions = [], timeout = 300, added_check = None):
	reactions.append("\U0000274C")
	
	def check_react(reaction, user):
		if ctx.author != user: return False
		return reaction.message == message and reaction.emoji in reactions 
	
	def check_message(message):
		if ctx.author != message.author: return False
		elif added_check: return added_check(message)
		return True
	
	message = await ctx.send(message)
	await add_multiple_reactions(message, reactions)
	
	done, pending = await asyncio.wait(
		[ctx.bot.wait_for("reaction_add", check = check_react, timeout = timeout),
		 ctx.bot.wait_for("message", check = check_message, timeout = timeout)], 
		return_when = asyncio.FIRST_COMPLETED
	)
	
	for future in pending: future.cancel()	#ignore anything else
	for future in done: future.exception() #retrieve and ignore any other completed future's exception
	
	try:
		result = done.pop().result()
	except asyncio.TimeoutError:
		raise await CommandCancelled.create("Command timed out", ctx)
	
	if isinstance(result, tuple) and result[0].emoji == "\U0000274C":
		raise await CommandCancelled.create("Command cancelled", ctx)
		
	return result
	
async def check_response(ctx, added_check, timeout = 300):
	#"hard" wait for that raises error on failure
	try:
		part = await ctx.bot.wait_for("message", timeout = timeout, check = lambda m: m.author == ctx.author)
	except asyncio.TimeoutError: 
		raise await CommandCancelled.create("Command timed out", ctx)
	if not added_check(part):
		raise BadMessageResponse("Content given internally is of invalid form")
		
	return part
	
async def add_multiple_reactions(message, reactions):
	return await asyncio.gather(*[message.add_reaction(r) for r in reactions])
	
class BadMessageResponse(Exception):
	pass
		
class CommandCancelled(commands.CommandError):
	@classmethod
	async def create(self, message, ctx):
		await ctx.send(f":x: | {message}.")
		return CommandCancelled(message)
		