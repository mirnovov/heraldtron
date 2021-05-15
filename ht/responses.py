import discord, asyncio
from discord.ext import commands
from . import utils

LONG_TIMEOUT = 1000
TIMEOUT = 300
SHORT_TIMEOUT = 150

async def respond_or_react(ctx, message, emojis = [], timeout = TIMEOUT, added_check = None):
	emojis.append("\U0000274C")
	
	def check_message(message):
		if ctx.author != message.author: return False
		elif added_check: return added_check(message)
		return True
	
	message = await ctx.send(message)
	await multi_react(message, emojis)
	
	done, pending = await asyncio.wait(
		[ctx.bot.wait_for("reaction_add", check = button_check(ctx, message, emojis), timeout = timeout),
		 ctx.bot.wait_for("message", check = check_message, timeout = timeout)], 
		return_when = asyncio.FIRST_COMPLETED
	)
	
	for future in pending: future.cancel()	#ignore anything else
	for future in done: future.exception() #retrieve and ignore any other completed future's exception
	
	try:
		result = done.pop().result()
	except asyncio.TimeoutError:
		raise await utils.CommandCancelled.create("Command timed out", ctx)
	
	if isinstance(result, tuple) and result[0].emoji == "\U0000274C":
		raise await utils.CommandCancelled.create("Command cancelled", ctx)
		
	return result
	
async def check(ctx, added_check, timeout = TIMEOUT):
	#"hard" wait for that raises error on failure
	try:
		part = await ctx.bot.wait_for("message", timeout = timeout, check = lambda m: m.author == ctx.author)
	except asyncio.TimeoutError: 
		raise await utils.CommandCancelled.create("Command timed out", ctx)
	if not added_check(part):
		raise utils.BadMessageResponse("Content given internally is of invalid form")
		
	return part
	
async def confirm(ctx, info, timeout = TIMEOUT):
	emojis = ("\U0000274C", "\U00002705") 
	
	message = await ctx.send(f"{info} React with :white_check_mark: to confirm or :x: to cancel.")
	await multi_react(message, emojis)
	
	try:
		reaction, user = await ctx.bot.wait_for(
			"reaction_add", 
			check = button_check(ctx, message, emojis), 
			timeout = timeout
		)
	except asyncio.TimeoutError:
		raise await utils.CommandCancelled.create("Command timed out", ctx)
		
	if isinstance(ctx.channel, discord.abc.GuildChannel): 
		await message.clear_reactions()
		
	if reaction.emoji == "\U0000274C":
		raise await utils.CommandCancelled.create("Command cancelled", ctx)
	else:
		await message.edit(content = ":white_check_mark: | Confirmed.")
		return True
		
async def multi_react(message, emojis):
	return await asyncio.gather(*[message.add_reaction(r) for r in emojis])

def button_check(ctx, message, emojis):		
	def _internal_check(reaction, user):
		if ctx.author != user: return False
		return reaction.message == message and reaction.emoji in emojis 
		
	return _internal_check
	