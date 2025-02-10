import json, random, functools, re, urllib
from discord import app_commands
from . import services, utils

class Source():
	register = {}
	cache = {}

	def __init__(self, name, desc):
		Source.register[name] = self
		
		self.choice = app_commands.Choice(name = desc, value = name)
		self.desc = desc

	def __call__(self, coroutine):
		self.retrieve = coroutine

	@staticmethod
	def random():
		return random.choice(list(Source.register.values()))

	@staticmethod
	@functools.cache
	def str_list():
		return "".join(f"- `{name}`: {artifact.desc}\n" for name, artifact in Source.register.items())
		
	@classmethod
	async def get_json_cached(cls, session, url, **kwargs):
		if url in cls.cache:
			return cls.cache[url]
		
		cls.cache[url] = await utils.get_json(session, url, **kwargs)
		return cls.cache[url]

SMTHS_IMG = re.compile(r"\<meta name=\"twitter\:image\" content=\"(.+)\" \/\>")
MATCH = re.compile(r"\<match\>|\<\/match\>")

@Source("rijks", "The Rijksmuseum, Amsterdam")
async def rijksmuseum(bot):
	api_key = bot.conf["AR_RIJKS"]
	collection = await Source.get_json_cached(
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

@Source("vanda", "The Victoria and Albert Museum, London")
async def victoria_and_albert(bot):
	query = random.choice(["%22heraldry%22+-brass", "%22coat%20of%20arms%22"])
	collection = await Source.get_json_cached(
		bot.session,
		f"https://api.vam.ac.uk/v2/objects/search?q={query}&page_size=100&year_made_to=1900&images_exist=1"
	)
	result = random.choice(collection["records"])

	return (
		f"https://collections.vam.ac.uk/item/{result['systemNumber']}/",
		result["_primaryTitle"] or result["objectType"],
		result["_primaryMaker"].get("name", ""),
		result["_images"]["_primary_thumbnail"].replace("!100,100","!800,"),
		None
	)

@Source("euro", "Europeana Pro")
async def europeana(bot):
	api_key = bot.conf["AR_EURO"]
	query = random.choice([
		"coat%20of%20arms", "wappen", "arms%20heraldry", "grb", "stemma", "brasão", "heraldiskt%20vapen",
		"vaakuna%20-hotelli", "címer", "wapen%20heraldik", "blazoen", "wapenschild", "wappen%20schild"
	])
	collection = await Source.get_json_cached(
		bot.session,
		f"https://api.europeana.eu/record/v2/search.json?query={query}&media=true&rows=100&wskey={api_key}"
	)
	result = random.choice(collection["items"])
	return (
		result["guid"],
		result["title"][0],
		"",
		result["edmPreview"][0],
		result["dataProvider"][0]
	)

@Source("dgtnz", "Digital NZ")
async def digital_nz(bot):
	api_key = bot.conf["AR_DGTNZ"]
	query = random.choice(["heraldry", "coat%20of%20arms"])
	collection = await Source.get_json_cached(
		bot.session,
		f"https://api.digitalnz.org/v3/records.json?api_key={api_key}&per_page=100&text={query}&and[category][]=Images"
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

@Source("met", "The Metropolitan Museum of Art, New York")
async def met_museum(bot):
	collection = await Source.get_json_cached(
		bot.session,
		"https://collectionapi.metmuseum.org/public/collection/v1/search?hasImages=true&q=%22coat%20of%20arms%22"
	)
	resultid = random.choice(collection["objectIDs"])
	result = await utils.get_json(
		bot.session,
		f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{resultid}"
	)

	return (
		result["objectURL"],
		result["title"],
		result["artistDisplayName"],
		result["primaryImageSmall"],
		None
	)

@Source("artic", "The Art Institute of Chicago, Chicago")
async def art_institute_chicago(bot):
	collection = await Source.get_json_cached(
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

@Source("smths", "The Smithsonian, Washington D.C.")
async def smithsonian(bot):
	api_key = bot.conf["AR_SMTHS"]
	collection = await Source.get_json_cached(
		bot.session,
		f"https://api.si.edu/openaccess/api/v1.0/search?q=coat%20of%20arms&rows=300&api_key={api_key}"
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

@Source("wiki", "Wikimedia Commons")
async def wikimedia_commons(bot):
	collection = await Source.get_json_cached(
		bot.session,
		"https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers"
		"&cmtype=file&cmtitle=Category:Paintings_of_coats_of_arms&format=json&cmlimit=500"
	)
	resultid = random.choice(collection["query"]["categorymembers"])["title"].replace("File:","")
	result = await services.commons(bot.session, bot.loop, resultid)

	return (
		result.find("urls").find("description").text,
		result.find("title").text,
		"",
		result.find("urls").find("file").text,
		None
	)

@Source("ddbtk", "Deutsche Digitale Bibliothek")
async def deutsche_digitale(bot):
	api_key = bot.conf["AR_DDBTK"]
	query = random.choice([
		"Heraldik&facet=objecttype_fct&objecttype_fct=Buchmalerei", "Wappen"
	])
	collection = await Source.get_json_cached(
		bot.session,
		f"https://api.deutsche-digitale-bibliothek.de/search?query={query}&type_fct=002&rows=700&oauth_consumer_key={api_key}"
	)
	result = random.choice(collection["results"][0]["docs"])

	return (
		f"https://www.deutsche-digitale-bibliothek.de/item/{result['id']}/",
		re.sub(MATCH, "", result["title"]),
		"",
		f"https://iiif.deutsche-digitale-bibliothek.de/image/2/{result['thumbnail']}/full/!800,600/0/default.jpg",
		None
	)

@Source("archive", "Internet Archive")
async def internet_archive(bot):
	collection = await Source.get_json_cached(
		bot.session,
		"https://archive.org/advancedsearch.php?q=(%22coat+of+arms%22)+AND+mediatype%3A(image)+AND+"
		"date%3A[1100-01-01+TO+1930-01-01]AND+-collection%3A(metropolitanmuseumofart-gallery)&fl[]"
		"=title&fl[]=identifier&fl[]=creator&fl[]=collection&rows=100&page=1&output=json"
	)
	result = random.choice(collection["response"]["docs"])
	
	result_data = await utils.get_json(bot.session, f"https://archive.org/metadata/{result['identifier']}")
	result_name = urllib.parse.quote(result_data['files'][0]['name']).replace("jp2", "jpg")
	result_image = f"https://{result_data['d1']}{result_data['dir']}/{result_name}"
	
	print(result_image)
	return (
		f"https://archive.org/details/{result['identifier']}/",
		result["title"][:255],
		result.get("creator", ""),
		result_image,
		result["collection"][0]
	)
