import urllib, os
from apiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from . import utils

def gis(query):
	load_dotenv()
	
	with build("customsearch","v1",developerKey=os.environ["GCS_TOKEN"]) as service:
		try:
			search = service.cse().list(
				q=query,
				cx=os.environ["GCS_CX"],
				searchType="image",
				safe = "off",
				num = 1
			).execute()

		except HttpError as error:
			reason = error._get_reason()
			
			if reason.startswith("Quota exceeded"):
				return utils.nv_embed(
					"Search quota exceeded",
					"The search quantity has exceeded the daily limit. Try again in a day."
				)
			
			return utils.nv_embed(
				"Invalid HTTP search request",
				"The image search API returned an incorrect HTTP request. According to Google, this"\
				f"is caused by: *{reason}*"
			)
			
	if "items" not in search:
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

def ds(blazon,drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = utils.get_json(f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	
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
	
def ds_catalog(charge):
	catalog = utils.get_json(f"https://drawshield.net/api/catalog/{urllib.parse.quote(charge)}")
	
	if not catalog.startswith("http"): return None
	return catalog