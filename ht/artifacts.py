import json, random, functools, re
from . import utils
from .ext import SlowTCPConnector

async def rijksmuseum(bot):
	api_key = bot.conf["AR_RIJKS"]
	collection = await utils.get_json(
		bot.session,
		f"https://www.rijksmuseum.nl/api/en/collection?key={api_key}&q=heraldry&ps=100&imgonly=True"
	)
	result = random.choice(collection["artObjects"])
	
	return (
		result["links"]["web"], 
		result["title"], 
		result["principalOrFirstMaker"],
		result["webImage"]["url"], 
		None
	)
	
async def victoria_and_albert(bot):
	collection = await utils.get_json(
		bot.session,
		f"https://api.vam.ac.uk/v2/objects/search?q=%22coat%20of%20arms%22&page_size=100&year_made_to=1900&images_exist=1"
	)
	result = random.choice(collection["records"])
	
	return (
		f"https://collections.vam.ac.uk/item/{result['systemNumber']}/", 
		result["_primaryTitle"], 
		result["_primaryMaker"]["name"],
		result["_images"]["_primary_thumbnail"].replace("!100,100","!800,"), 
		None
	)
	
async def europeana(bot):
	api_key = bot.conf["AR_EURO"]
	collection = await utils.get_json(
		bot.session,
		f"https://api.europeana.eu/record/v2/search.json?query=coat%20of%20arms&media=true&rows=100&wskey={api_key}"
	)
	result = random.choice(collection["items"])
	return (
		result["guid"], 
		result["title"][0], 
		"",
		result["edmPreview"][0], 
		result["dataProvider"][0]
	)
	
async def digital_nz(bot):
	api_key = bot.conf["AR_DGTNZ"]
	collection = await utils.get_json(
		bot.session,
		f"https://api.digitalnz.org/v3/records.json?api_key={api_key}&per_page=100&text=heraldry&and[category][]=Images"
	)
	results = collection["search"]["results"]
	result = {"thumbnail_url": None}
	
	while result["thumbnail_url"] is None:
		#no way to filter the results so only items with images appear
		result = random.choice(results)
		
	return (
		result["landing_url"], 
		result["title"], 
		"",
		result["thumbnail_url"], 
		result["display_content_partner"]
	)

async def met_museum(bot):
	async with SlowTCPConnector.get_slow_session() as slow_session:
		collection = await utils.get_json(
			slow_session,
			"https://collectionapi.metmuseum.org/public/collection/v1/search?hasImages=true&q=%22coat%20of%20arms%22"
		)
		resultid = random.choice(collection["objectIDs"])
		result = await utils.get_json(
			slow_session,
			f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{resultid}"
		)
	
	return (
		result["objectURL"], 
		result["title"], 
		result["artistDisplayName"],
		result["primaryImageSmall"], 
		None
	)
	
async def art_institute_chicago(bot):
	collection = await utils.get_json(
		bot.session,
		"https://api.artic.edu/api/v1/artworks/search?q=coat%20of%20arms&limit=100&fields=id,title,image_id,artist_title"
	)
	result = random.choice(collection["data"])
		
	return (
		f"https://www.artic.edu/artworks/{result['id']}/", 
		result["title"], 
		result["artist_title"],
		f"https://www.artic.edu/iiif/2/{result['image_id']}/full/843,/0/default.jpg", 
		None
	)

SMTHS_IMG = re.compile("\<meta name=\"twitter\:image\" content=\"(.+)\" \/\>")
	
async def smithsonian(bot):
	api_key = bot.conf["AR_SMTHS"]
	collection = await utils.get_json(
		bot.session,
		f"https://api.si.edu/openaccess/api/v1.0/search?q=coat%20of%20arms&rows=400&api_key={api_key}"
	)
	results = collection["response"]["rows"]
	
	while True: #random choice may seem bad, but checking all 400 is worse
		result = random.choice(results)
		if "online_media_type" in result["content"]["indexedStructured"]: break
		
	url = f"https://www.si.edu/object/{result['url']}/"
	
	#the image isn't provided by the api, so scrape the html :(
	html = await utils.get_text(bot.session,url)
	image_url = re.search(SMTHS_IMG, html)[1]
	
	return (url, result["title"], "", image_url, None)
	
async def wikimedia_commons(bot):
	collection = await utils.get_json(
		bot.session,
		"https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtype=file&cmtitle=Category:Paintings_of_coats_of_arms&format=json&cmlimit=500"
	)
	resultid = random.choice(collection["query"]["categorymembers"])["title"].replace("File:","")
	result_text = await utils.get_text(
		bot.session,
		f"https://magnus-toolserver.toolforge.org/commonsapi.php?image={resultid}&thumbwidth=600&thumbheight=600&meta"
	)
	result = await bot.loop.run_in_executor(None, utils.parse_xml,result_text,"file")
	
	return (
		result.find("urls").find("description").text, 
		result.find("title").text, 
		"", 
		result.find("urls").find("file").text, 
		None
	)
	
async def deutsche_digitale(bot):
	api_key = bot.conf["AR_DDBTK"]
	collection = await utils.get_json(
		bot.session,
		f"https://api.deutsche-digitale-bibliothek.de/search?query=Heraldik&facet=objecttype_fct&rows=1000&objecttype_fct=Buchmalerei&type_fct=002&oauth_consumer_key={api_key}"
	)
	result = random.choice(collection["results"][0]["docs"])
	
	return (
		f"https://www.deutsche-digitale-bibliothek.de/item/{result['id']}/", 
		result["title"], 
		"",
		f"https://iiif.deutsche-digitale-bibliothek.de/image/2/{result['thumbnail']}/full/!800,600/0/default.jpg", 
		None
	)
	
source_list = {
	"rijks": (rijksmuseum, "The Rijksmuseum, Amsterdam"),
	"vanda": (victoria_and_albert, "The Victoria and Albert Museum, London"),
	"euro": (europeana, "Europeana Pro"),
	"dgtnz": (digital_nz, "Digital NZ"),
	"met": (met_museum, "The Metropolitan Museum of Art, New York"),
	"artic": (art_institute_chicago, "The Art Institute of Chicago, Chicago"),
	"smths": (smithsonian, "The Smithsonian, Washington D.C."),
	"wiki": (wikimedia_commons, "Wikimedia Commons"),
	"ddbtk": (deutsche_digitale, "Deutsche Digitale Bibliothek"),
}

@functools.cache
def source_string():
	string = ""
	
	for source, name in source_list.items():
		string += f"- `{source}`: {name[1]}\n"
	return string
