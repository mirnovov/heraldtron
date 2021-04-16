import urllib, os
from dotenv import load_dotenv
from . import utils

async def gis(query):
	load_dotenv()
	
	params = urllib.parse.urlencode({
		"key": os.environ["GCS_TOKEN"],
		"q": query,
		"cx": os.environ["GCS_CX"],
		"searchType": "image",
		"safe": "off",
		"num": 1
	})
	
	search = await utils.get_json(f"https://www.googleapis.com/customsearch/v1?{params}")
	
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
	
	embed = utils.nv_embed(
		f"Result for \"{query}\"",
		f"[{search['items'][0]['title']}]({search['items'][0]['image']['contextLink']})",
		kind=3,
		custom_name="Google image search"
	)
	embed.set_image(url=search["items"][0]["link"])	
	embed.set_footer(text=f"Search conducted using the Google Custom Search API in {search['searchInformation']['formattedSearchTime']}s.")
	return embed

async def ds(blazon,drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = await utils.get_json(f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	
	embed = utils.nv_embed("",blazon,kind=4,custom_name=f"{drawn_kind} drawn!")		
	embed.set_image(url=f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=png&dummy=shield.png")
	embed.set_footer(text=f"Drawn using DrawShield; © Karl Wilcox. ")
	
	for message in results["messages"]:
		if message["category"] != "blazon": continue
		elif "linerange" in message:
			embed.add_field(name=f"Error {message['linerange']}",value=message["content"],inline=False)
		elif "context" in message:
			embed.add_field(name="Error",value=f"{message['content']} {message['context']}",inline=False)
			
	return embed
	
async def ds_catalog(charge):
	catalog = await utils.get_json(f"https://drawshield.net/api/catalog/{urllib.parse.quote(charge)}")
	
	if not catalog.startswith("http"): return None
	return catalog