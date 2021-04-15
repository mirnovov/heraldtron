import urllib
from . import utils

def gis(query):
	embed = utils.nv_embed(
		f"Results for \"{charge}\"",
		"",
		kind=3,
		custom_name="Google image search"
	)
	#todo
	
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