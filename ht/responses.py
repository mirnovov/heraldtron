import discord, asyncio
from discord.ext import commands
from . import utils

LONG_TIMEOUT = 1000
TIMEOUT = 300
SHORT_TIMEOUT = 150

async def check(ctx, added_check, timeout = TIMEOUT):
	#"hard" wait for that raises error on failure
	try:
		part = await ctx.bot.wait_for("message", timeout = timeout, check = lambda m: m.author == ctx.author)
	except asyncio.TimeoutError: 
		raise await utils.CommandCancelled.create("Command timed out", ctx)
	if not added_check(part):
		raise utils.BadMessageResponse("Content given internally is of invalid form")
		
	return part
		
async def choice(ctx, values, emojis, embed_type, embed_title, embed_heading, action_description):
	embed = embed_type.create(embed_title, "", heading = embed_heading)
	emojis_constrained = emojis[:len(values)]
	emojis_full = ("\U0000274C", *emojis_constrained)
	
	for emoji, value in zip(emojis_constrained, values):
		embed.description += f"- {emoji} {value}\n"
	
	embed.description += f"\nReact with an emoji to {action_description}, or :x: to cancel."
	message = await ctx.send(embed = embed)
	await multi_react(message, emojis_full)
	
	try:
		reaction, user = await ctx.bot.wait_for(
			"reaction_add", 
			check = button_check(ctx, message, emojis_full),
			timeout = TIMEOUT
		)		
	except asyncio.TimeoutError: 
		raise await utils.CommandCancelled.create("Command timed out", ctx)
	
	if reaction.emoji == emojis_full[0]:
		raise await utils.CommandCancelled.create("Command cancelled", ctx)
	else:
		return emojis_constrained.index(reaction.emoji)
		
async def multi_react(message, emojis):
	return await asyncio.gather(*[message.add_reaction(r) for r in emojis])

def button_check(ctx, message, emojis):		
	def _internal_check(reaction, user):
		if ctx.author != user: return False
		return reaction.message == message and reaction.emoji in emojis 
		
	return _internal_check
	