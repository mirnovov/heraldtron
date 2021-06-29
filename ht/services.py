import discord, asyncio, urllib, io, base64
from xml.etree import ElementTree
from . import embeds, utils, views

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
	
	if search == None: raise utils.CustomCommandError(
		"Invalid HTTP search request",
		"The image search API returned an incorrect HTTP request."
		"This might be caused by the search amount exceeding the maximum quota."
	)	
	elif "items" not in search: raise utils.CustomCommandError(
		"Search has no results",
		"The search returned no images. Check that what you are looking for exists."
	)
	
	def image_result(item):
		url = discord.utils.escape_markdown(item["image"]["contextLink"])
		embed = embeds.SEARCH_RESULT.create(
			f"Results for \"{query}\"",
			f"[{item['title']}]({url})",
			heading = "Google image search"
		)
		embed.set_image(url = item["link"])
		embed.set_footer(
			text = "Search conducted using the Google Custom Search API "
				  f"in {search['searchInformation']['formattedSearchTime']}s."
		)
		return embed
	
	pages = tuple(image_result(page) for page in search["items"])
	await ctx.send(embed = pages[0], view = views.Navigator(pages))

async def ds(session, blazon, drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = await utils.get_json(session, f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	image = discord.File(io.BytesIO(base64.b64decode(results["image"])), filename = "ds.png")
	
	embed = embeds.DRAW.create("", f"*{blazon}*", heading = f"{drawn_kind} drawn!")	
	embed.set_image(url = "attachment://ds.png")	
	embed.set_footer(text = f"Drawn using DrawShield; © Karl Wilcox. ")
	
	for message in results["messages"]:
		if message["category"] != "blazon": continue
		elif "linerange" in message:
			embed.add_field(name = f"Error {message['linerange'].strip()}", value = message["content"], inline = False)
		elif "context" in message:
			embed.add_field(name = "Error", value = f"{message['content']} {message['context']}", inline = False)
			
	return embed, image
	
async def ds_catalog(session, charge):
	catalog = await utils.get_json(session, f"https://drawshield.net/api/catalog/{urllib.parse.quote(charge)}")
	
	if not catalog.startswith("http"): return None
	return catalog.split("\n")
	
async def commons(session, loop, filename):
	result_text = await utils.get_text(
		session,
		f"https://magnus-toolserver.toolforge.org/commonsapi.php?image={filename}&thumbwidth=600&thumbheight=600&meta"
	)
	get_json = lambda text_string, root: ElementTree.fromstring(text_string).find(root)
	
	return await loop.run_in_executor(None, get_json, result_text, "file")