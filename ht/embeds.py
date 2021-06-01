import discord, asyncio, random
from enum import Enum
from discord.ext import commands
from . import responses

DEFAULT = 0x444850

class Theme(Enum):
	ERROR = (0xdd3333, "4/4e/OOjs_UI_icon_error-destructive.svg/200px-OOjs_UI_icon_error-destructive.svg.png", "An error has been encountered")
	MOD_MESSAGE = (0xff5d01, "4/4c/OOjs_UI_icon_notice-warning.svg/240px-OOjs_UI_icon_notice-warning.svg.png", "Official moderator message")
	HELP = (0x3365ca, "5/5f/OOjs_UI_icon_info-progressive.svg/240px-OOjs_UI_icon_info-progressive.svg.png", "Command help")
	SEARCH_RESULT = (0x444850, "8/8c/OOjs_UI_icon_search-ltr-invert.svg/240px-OOjs_UI_icon_search-ltr-invert.svg.png", "Search result")
	GENERIC = (DEFAULT, "5/5e/VisualEditor_icon_reference-rtl-invert.svg/240px-VisualEditor_icon_reference-invert.svg.png", "Result")
	ABOUT = (0x02af89, "4/4e/Echo_gratitude.svg/240px-Echo_gratitude.svg.png", "About Heraldtron")
	FLAG_FACT = (DEFAULT, "1/14/OOjs_UI_icon_flag-ltr-invert.svg/200px-OOjs_UI_icon_flag-ltr-invert.svg.png", "Flag fact")
	FEED = (DEFAULT, "2/21/OOjs_UI_icon_feedback-ltr-invert.svg/240px-OOjs_UI_icon_feedback-ltr-invert.svg.png", "Reddit post")
	USER_INFO = (DEFAULT, "d/d4/VisualEditor_icon_profile-invert.svg/240px-VisualEditor_icon_profile-invert.svg.png", "User")
	CHOICE = (DEFAULT, "d/df/OOjs_UI_icon_next-ltr-invert.svg/240px-OOjs_UI_icon_next-ltr-invert.svg.png", "Choice required")
	DRAW = (DEFAULT, "d/d2/OOjs_UI_icon_edit-rtl-invert.svg/240px-OOjs_UI_icon_edit-rtl-invert.svg.png", "Drawn!")
	
	def __init__(self, colour, icon_url, heading):
		self.colour = colour
		self.icon_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{icon_url}" 
		self.heading = heading
	
	def create(self, title, desc, heading = None):
		embed = discord.Embed(title = title, description = desc)
		embed.colour = self.colour
		embed.set_author(name = heading or self.heading, icon_url = self.icon_url)
		
		return embed	

#this is done in the default random class				
ERROR = Theme.ERROR
MOD_MESSAGE = Theme.MOD_MESSAGE
HELP = Theme.HELP
SEARCH_RESULT = Theme.SEARCH_RESULT
GENERIC = Theme.GENERIC
ABOUT = Theme.ABOUT
FLAG_FACT = Theme.FLAG_FACT
FEED = Theme.FEED
USER_INFO = Theme.USER_INFO
CHOICE = Theme.CHOICE
DRAW = Theme.DRAW

async def paginate(ctx, embed_function, embeds_size):
	message = await ctx.send(embed = embed_function(0))		
	emojis = ("\U000023EE\U0000FE0F", "\U00002B05\U0000FE0F", "\U0001F500", "\U000027A1\U0000FE0F", "\U000023ED\U0000FE0F")
	index = 0
	await responses.multi_react(message, emojis)
	
	while True:
		try:
			reaction, user = await ctx.bot.wait_for(
				"reaction_add", 
				check = responses.button_check(ctx, message, emojis),
				timeout = responses.SHORT_TIMEOUT
			)
			updated = await message.channel.fetch_message(message.id)
			
			if reaction.emoji == emojis[0]: index = 0
			elif reaction.emoji == emojis[1] and index > 0: index -= 1
			elif reaction.emoji == emojis[2]: index = random.randrange(0, embeds_size - 1)
			elif reaction.emoji == emojis[3] and index < embeds_size - 1: index += 1
			elif reaction.emoji == emojis[4]: index = embeds_size - 1
			
			await message.edit(embed = embed_function(index))
			
			if isinstance(ctx.channel, discord.abc.GuildChannel):
				await message.remove_reaction(reaction, ctx.author)
			
		except asyncio.TimeoutError:
			await message.edit(content=":x: | The paged command has timed out.")
			if isinstance(ctx.channel, discord.abc.GuildChannel): 
				await message.clear_reactions()
			return
