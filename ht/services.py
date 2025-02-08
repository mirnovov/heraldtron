import discord, asyncio, base64, html, io, itertools, random, urllib
from discord import ui
from collections import defaultdict
from datetime import datetime, timezone, timedelta
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
	await views.Navigator(ctx, pages).run()

async def ds(session, blazon, drawn_kind):
	blazon_out = urllib.parse.quote(blazon)
	results = await utils.get_json(session, f"https://drawshield.net/include/drawshield.php?blazon={blazon_out}&outputformat=json")
	image = discord.File(io.BytesIO(base64.b64decode(results["image"])), filename = "ds.png")

	embed = embeds.DRAW.create("", f"*{blazon}*", heading = f"{drawn_kind} drawn!")
	embed.set_image(url = "attachment://ds.png")
	embed.set_footer(
		icon_url = "https://drawshield.net/img/shop-logo.png",
		text = f"Not all blazons can be illustrated with this command.\nDrawn using DrawShield; © Karl Wilcox."
	)

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
	
async def trivia(ctx, question):
	TRIVIA_LENGTH = 22
	
	name = html.unescape(question["question"])
	info = f"**{html.unescape(question['category'])}** | {question['difficulty'].capitalize()}\n\n"
	countdown = datetime.now(tz = timezone.utc) + timedelta(seconds = TRIVIA_LENGTH)
	
	embed = embeds.GENERIC.create(name, info, heading = "Trivia")
	embed.description += f"The correct answer will appear <t:{countdown.timestamp():.0f}:R>."
	embed.set_footer(text = f"Courtesy of the Open Trivia Database.")
	
	view = ui.View()
	users = {}
	answers = question["incorrect_answers"]
	correct = random.randrange(0, len(answers) + 1)
	
	answers.insert(correct, question["correct_answer"])
	
	for answer in answers:
		view.add_item(views.TriviaButton(answer, users))
	
	message = await ctx.send(embed = embed, view = view)
	await asyncio.sleep(TRIVIA_LENGTH)
	
	embed.description = f"{info}The correct answer is: **{html.unescape(answers[correct])}**"
	updated = await message.channel.fetch_message(message.id)
	if updated is None: return #message deleted
	
	results = defaultdict(list)
	stats = ""
	
	for user, answer in users.items():
		results[answer].append(user)
		
	for answer, users in results.items():
		stats += f"- {answer}: {','.join(users)} (**{len(users)}**)\n"

	if stats: embed.description += f"\n\n**Responses:**\n\u0020{stats}"
	await message.edit(embed = embed, view = None)

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
		edit_link = f"[Edit on Heraldicon]({success['edit-url']})"
		embed = embeds.DRAW.create("", edit_link, heading = "Shield created!")
		image_data = await utils.get_bytes(session, png_url)
		image = discord.File(image_data, filename = "heraldicon-arms.png")
		embed.set_image(url = "attachment://heraldicon-arms.png")
		embed.add_field(name = "Blazon", value = f"*{blazon}*", inline = True)
		embed.set_footer(
			icon_url = "https://cdn.heraldicon.org/img/heraldicon-logo-discord.png",
			text = "Drawn using Heraldicon; licensed under CC BY-SA 4.0 (attribution on https://heraldicon.org)"
		)
		return embed, image

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
	embed = embeds.ERROR.create("Blazon could not be parsed", error_message)
	embed.add_field(name = "blazon", value = f"*{blazon}*", inline = True)

	return embed, None

async def heraldicon_options(session):
	def add_option_type(embed, source, name):
		embed.add_field(
			name = name,
			value = " ".join(f"`+{x}`" for x in source),
			inline = False
		)

	result = await utils.post_json(
		session,
		"https://heraldicon.org/api",
		{"call": "blazon-options"}
	)
	if "success" in result:
		embed = embeds.DRAW.create(
			"",
			"Put any of these options as first words before the blazon.",
			heading = "Heraldicon rendering options"
		)

		add_option_type(embed, result["success"]["options"]["miscellaneous"], "General")
		add_option_type(embed, result["success"]["options"]["mode"], "Mode")
		add_option_type(embed, result["success"]["options"]["escutcheon"], "Escutcheons")
		add_option_type(embed, result["success"]["options"]["theme"], "Themes")
		add_option_type(embed, result["success"]["options"]["texture"], "Textures")

		embed.set_footer(
			icon_url = "https://cdn.heraldicon.org/img/heraldicon-logo-discord.png",
			text = "For more info, see https://heraldicon.org"
		)
		return embed

	raise utils.CustomCommandError(
		"Cannot retrieve Heraldicon options",
		"An unknown error occurred while trying to retrieve the Heraldicon options."
	)
