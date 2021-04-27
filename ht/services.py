import discord, urllib, os, io, base64, random, asyncio
from . import utils

async def gis(ctx, query):
	IMAGE_NUM = 10
	params = urllib.parse.urlencode({
		"key": ctx.bot.conf["GCS_TOKEN"],
		"q": query,
		"cx": ctx.bot.conf["GCS_CX"],
		"searchType": "image",
		"safe": "off",
		"num": IMAGE_NUM
	})
	
	search = await utils.get_json(ctx.bot.session, f"https://www.googleapis.com/customsearch/v1?{params}")
	
	if search == None:
		return utils.nv_embed(
			"Invalid HTTP search request",
			"The image search API returned an incorrect HTTP request."\
			"This might be caused by the search amount exceeding the maximum quota."
		)		
	elif "items" not in search:
		return utils.nv_embed(
			"Search has no results",
			"The search returned no images. Check that what you are looking for exists."
		)
	
	def image_result(index):
		item = search["items"][index]
		embed = utils.nv_embed(
			f"Results for \"{query}\"",
			f"[{item['title']}]({item['image']['contextLink']})",
			kind=3,
			custom_name=f"Google image search ({index + 1}/{IMAGE_NUM})"
		)
		embed.set_image(url=item["link"])	
		embed.set_footer(text=f"Search conducted using the Google Custom Search API in {search['searchInformation']['formattedSearchTime']}s.")
		return embed
	
	message = await ctx.send(embed=image_result(0))
	
	if not isinstance(ctx.channel, discord.abc.GuildChannel):
		return #doesn't work in dms 
		
	buttons = ("\U000023EE","\U00002B05","\U0001F500","\U000027A1","\U000023ED")
	index = 0
	await asyncio.gather(*[message.add_reaction(r) for r in buttons])
	
	def check_react(reaction, user):
		if ctx.author != user: return False
		return reaction.message == message
	
	while True:
		try:
			reaction, user = await ctx.bot.wait_for("reaction_add", timeout=120, check=check_react)
			updated = await message.channel.fetch_message(message.id)
			
			if reaction.emoji == buttons[0]: index = 0
			elif reaction.emoji == buttons[1] and index > 0: index -= 1
			elif reaction.emoji == buttons[2]: index = random.randrange(0,IMAGE_NUM - 1)
			elif reaction.emoji == buttons[3] and index < IMAGE_NUM - 1: index += 1
			elif reaction.emoji == buttons[4]: index = IMAGE_NUM - 1
			
			await message.edit(embed=image_result(index))
			await message.remove_reaction(reaction,ctx.author)
		except asyncio.TimeoutError:
			await message.edit(content="**The image search session has timed out.**")
			await message.clear_reactions()		
			return

async def ds(session, blazon, drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = await utils.get_json(session, f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	image = discord.File(io.BytesIO(base64.b64decode(results["image"])),filename="ds.png")
	
	embed = utils.nv_embed("",f"*{blazon}*",kind=4,custom_name=f"{drawn_kind} drawn!")	
	embed.set_image(url="attachment://ds.png")	
	embed.set_footer(text=f"Drawn using DrawShield; © Karl Wilcox. ")
	
	for message in results["messages"]:
		if message["category"] != "blazon": continue
		elif "linerange" in message:
			embed.add_field(name=f"Error {message['linerange']}",value=message["content"],inline=False)
		elif "context" in message:
			embed.add_field(name="Error",value=f"{message['content']} {message['context']}",inline=False)
			
	return embed, image
	
async def ds_catalog(session, charge):
	catalog = await utils.get_json(session, f"https://drawshield.net/api/catalog/{urllib.parse.quote(charge)}")
	
	if not catalog.startswith("http"): return None
	return catalog