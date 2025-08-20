import discord, asyncio, base64, collections, html, io, itertools, random, urllib
from discord import ui
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree
from . import utils, views

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
		gallery = ui.MediaGallery()
		gallery.add_item(media = item["link"])
		
		items = [
			ui.TextDisplay(
				f"### Results for \"{query}\"\n"
				f"[{item['title']}]({url})"
			),
			gallery
		]
		return items

	pages = tuple(image_result(page) for page in search["items"])
	await views.Navigator(
		ctx, 
		pages,
		header = f":frame_photo: Google image search",
	).run()

async def ds(session, blazon, drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = await utils.get_json(session, f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	image = discord.File(io.BytesIO(base64.b64decode(results["image"])), filename = "ds.png")

	view = views.Generic("", f"### *{blazon}*", heading = f":pencil2: {drawn_kind} drawn!")
	view.add_image("attachment://ds.png")
	view.add_footer("Not all blazons can be illustrated with this command.\n-# Drawn using DrawShield; © Karl Wilcox.")

	errors = []

	for message in results["messages"]:
		if not message["category"] in ["parser", "blazon"]: continue
		elif "linerange" in message:
			errors.append(f"{message['linerange'].strip()}: {message['content']}")
		elif "content" in message:
			errors.append(message['content'])
			
	if errors:
		view.add_text(f"\n\n-# {views.ERROR_EMOJI} **Errors have been encountered**\n{'\n'.join(errors)}")

	return view, image

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
	
async def trivia(ctx, interaction, question):
	TRIVIA_LENGTH = 22
	
	name = html.unescape(question["question"])
	info = f"-# **{html.unescape(question['category'])}** \n-# {question['difficulty'].capitalize()}\n\u200b"
	countdown = datetime.now(tz = timezone.utc) + timedelta(seconds = TRIVIA_LENGTH)
	
	view = views.Generic(name, info, heading = ":interrobang: Trivia")
	actionrow = ui.ActionRow()
	display = ui.TextDisplay(f"The correct answer will appear <t:{countdown.timestamp():.0f}:R>.\n\u200b")
	
	view.container.add_item(actionrow)
	view.container.add_item(display)
	view.add_footer(text = f"Courtesy of the [Open Trivia Database](https://opentdb.com).")
	
	users = {}
	answers = question["incorrect_answers"]
	correct = random.randrange(0, len(answers) + 1)
	
	answers.insert(correct, question["correct_answer"])
	
	for answer in answers:
		actionrow.add_item(views.TriviaButton(answer, users))
	
	if ctx:
		message = await ctx.send(view = view)
	else:
		await interaction.response.send_message(view = view)
		message = interaction.message
		
	await asyncio.sleep(TRIVIA_LENGTH)
	
	view.container.remove_item(actionrow)
	display.content = f"\n\u2000The correct answer is: **{html.unescape(answers[correct])}**"
	
	results = defaultdict(list)
	stats = ""
	
	for user, answer in users.items():
		results[answer].append(user)
		
	for answer, users in results.items():
		stats += f"- {answer}: {','.join(users)} (**{len(users)}**)\n"

	if stats: display.content += f"\n### Responses\n{stats}"
	
	try:
		if ctx:
			await message.edit(view = view)
		else:
			await interaction.edit_original_response(view = view)
	except discord.NotFound:
		pass

async def heraldicon(session, query):
	def is_option_keyword(s):
		return s.startswith(":") or s.startswith("+")
	
	def parse_options_and_blazon(query):
		words = query.split()
		options = list(x.lower() for x in itertools.takewhile(is_option_keyword, words))
		blazon = " ".join(itertools.dropwhile(is_option_keyword, words))
		return options, blazon

	options, blazon = parse_options_and_blazon(query)
	result = await utils.post_json(session, "https://heraldicon.org/api",
		{
			"call": "generate-from-blazon",
			"data": {
				"blazon": blazon,
				"options": options,
			},
		}
	)
	success = result.get("success")
	if success:
		png_url = success["png-url"]
		view = views.Generic(
			"", 
			f"### *{blazon}*", 
			heading = ":pencil2: Shield created!"
		)
		
		image_data = await utils.get_bytes(session, png_url)
		image = discord.File(image_data, filename = "heraldicon-arms.png")
		
		view.add_image("attachment://heraldicon-arms.png")

		view.add_footer(
			"Drawn using Heraldicon; licensed under CC BY-SA 4.0\n"
			"-# Attribution on [heraldicon.org](https://heraldicon.org)"
		)
		
		view.container.add_item(ui.ActionRow(ui.Button(
			label = "Edit on Heraldicon",
			url = success["edit-url"]
		)))
		
		return view, image

	index = result["error"]["data"]["index"]
	blazon = result["error"]["data"]["blazon"]
	choices = result["error"]["data"]["suggestions"]

	show_before = 20
	show_after = 10
	relevant_chunk = blazon[max(index - show_before, 0):index]
	bad_words = blazon[index:index + show_after]
	if index > show_before:
		relevant_chunk = "... " + relevant_chunk
	if index + show_after < len(blazon):
		bad_words += "..."
	arrow = "-" * (1 + len(relevant_chunk)) + "^"
	suggestions = [x[0] for x in choices[:20]]
	error_message = f"""```Got confused by:
'{relevant_chunk}{bad_words}'
{arrow}

Suggestions:
{', '.join(suggestions)}
	```"""
	raise utils.CustomCommandError(
		"Blazon could not be parsed",
		f"{error_message}\n### Blazon\n*{blazon}*"
	)

async def heraldicon_options(session):
	def add_option_type(view, source, name):
		view.add_text(
			f"\n### {name}\n" +
			" ".join(f"`+{x}`" for x in source)
		)

	result = await utils.post_json(
		session,
		"https://heraldicon.org/api",
		{"call": "blazon-options"}
	)
	if "success" in result:
		view = views.Generic(
			"",
			"-# Put any of these options as first words before the blazon. "
			"For more info, see [heraldicon.org](https://heraldicon.org).",
			heading = ":pencil2: Heraldicon rendering options"
		)

		add_option_type(view, result["success"]["options"]["miscellaneous"], "General")
		add_option_type(view, result["success"]["options"]["mode"], "Mode")
		add_option_type(view, result["success"]["options"]["escutcheon"], "Escutcheons")
		add_option_type(view, result["success"]["options"]["theme"], "Themes")
		add_option_type(view, result["success"]["options"]["texture"], "Textures")

		return view

	raise utils.CustomCommandError(
		"Cannot retrieve Heraldicon options",
		"An unknown error occurred while trying to retrieve the Heraldicon options."
	)
	
async def hero(session, term):
	async def get_image(session, url):
		image_url = url.removeprefix("http://www.yso.fi/onto/hero/p") + ".png"
		full_url =  "https://heraldica.narc.fi/img/hero/thumb/" + image_url
		
		async with session.get(full_url, ssl = False) as source:
			if str(source.status)[0] != "2": return None 
			
			image = await source.read()
			bytes = io.BytesIO(image)
		
		image = discord.File(bytes, filename = image_url)
		
		return image

	def get_labels(result, key):
		#Annoyingly, lists of one item are represented as just the item, so this solves that
		a = result.get(key, [])
		if type(a) == dict: return [a]
		return a
	
	def sort_results(item):
		if item == "**Primary**": return -999
		elif item == "Other names": return 998
		elif item == "Other languages": return 999
		
		return ord(item[0])

	query = await utils.get_json(session,
		f"http://api.finto.fi/rest/v1/search?vocab=hero&query={urllib.parse.quote(term)}&lang=en"
	)
	
	if len(query["results"]) == 0:
		return None, None
	
	uri = query["results"][0]["uri"]
	
	results = (await utils.get_json(session,
		f"http://api.finto.fi/rest/v1/hero/data?format=application%2Fjson&uri={urllib.parse.quote(uri)}&lang=en"
	))["graph"]
	
	description_text = "### HERO ontology\n"
	descriptions = collections.defaultdict(list)
	image = None
	
	for result in results:
		if result["uri"] == "http://www.yso.fi/onto/hero/": continue
		elif result["uri"] == uri: result_type = "**Primary**"
		elif result.get("narrower"): result_type = "Broader"
		elif result.get("broader"): result_type = "Narrower"
		else: result_type = "Related"
	
		result_name = "(unknown)"
		pref_labels = get_labels(result, "prefLabel")
	
		if pref_labels:
			en_labels = [a for a in pref_labels if a["lang"] == "en"]
			
			if en_labels:
				result_name = en_labels[0]["value"]
			else:
				label = pref_labels[0]
				result_name = f"*{label['value']}* ({label['lang']})"
		
		en_uri = result["uri"].replace("http://www.yso.fi/onto/hero/", "http://finto.fi/hero/en/page/")

		if result_type == "**Primary**":
			image = await get_image(session, uri)
			result_name = f"**{result_name}**"
			
			descriptions["Other names"] = [a["value"] for a in get_labels(result, "altLabel") if a["lang"] == "en"]
			descriptions["Other languages"] = [
				f"*{a['value']}* ({a['lang']})" 
				for a in sorted(pref_labels, key = lambda a: a["lang"]) 
				if a["lang"] != "en"
			]
		
		descriptions[result_type].append(f"[{result_name}]({en_uri})")
	
	for result_type in sorted(descriptions, key = sort_results):
		results = descriptions[result_type]
		if not results: continue
		
		description_text += f"- {result_type}: {' \u00B7 '.join(results)}\n"

	return description_text, image
