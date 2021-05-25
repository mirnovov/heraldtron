import discord, urllib, time, re, random, os
from docx2python import docx2python
from datetime import datetime, timezone
from discord.ext import commands, tasks
from .. import utils, embeds

class BotTasks(commands.Cog, name = "Bot tasks"):
	STRIP_SPACES = re.compile(r"\n[\t\s]+")
	FIND_DATA = re.compile(r"GreiiN:(\d+) - (?:[^\n\r#]+\n)?(.+)#(\d+)[\s\S]+?(Blazon[\s\S]+?)(?=GreiiN|$)")
	
	STATUSES = (
		discord.Game("a !challenge"),
		discord.Game("with a !resource"),
		discord.Game("with !drawshield"),
		discord.Game("with fire"),
		discord.Game("cards"),
		discord.Game("bingo"),
		discord.Game("canasta"),
		discord.Game("Monopoly"),
		discord.Activity(type = discord.ActivityType.listening, name="for !help"),
		discord.Activity(type = discord.ActivityType.listening, name="a !motto"),
		discord.Activity(type = discord.ActivityType.listening, name="the sounds of nature"),
		discord.Activity(type = discord.ActivityType.watching, name="an !armiger"),
		discord.Activity(type = discord.ActivityType.watching, name="heraldic documentaries"),
		discord.Activity(type = discord.ActivityType.watching, name="Manos: The Hands of Fate"),
		discord.Activity(type = discord.ActivityType.watching, name="Puparia"),
		discord.Activity(type = discord.ActivityType.competing, name="a !trivia game")
	)
	
	def __init__(self, bot):
		self.bot = bot
		self.get_reddit_posts.start()
		self.update_info.start()
		self.sync_book.start()
		
		if not os.path.isdir("data/book"):
			os.mkdir("data/book")
		
	def cog_unload(self):
		self.get_reddit_posts.stop()
		self.sync_book.stop()
		self.update_info.stop()
		
	@tasks.loop(hours = 12)
	async def update_info(self):
		now = datetime.now().date()
		last = await self.bot.dbc.store_get("last_avatar")
		
		if now.month == 6 and now.day in range(8, 12):
			await self.update_avatar(self.bot, "media/avatars/ihd.jpg", last)
			await self.bot.change_presence(activity = discord.Game(":shield: International Heraldry Day"))
		
		elif now.month == 6:
			await self.update_avatar(self.bot, "media/avatars/pride.jpg", last)
			await self.bot.change_presence(activity = discord.Game(":rainbow_flag: Happy Pride Month!"))
			
		elif now.month == 12:
			await self.update_avatar(self.bot, "media/avatars/holiday.jpg", last)
			await self.bot.change_presence(activity = discord.Game(":christmas_tree: Happy Holidays!"))
			
		elif now.month == 4:
			await self.update_avatar(self.bot, "media/avatars/easter.jpg", last)
			await self.bot.change_presence(activity = discord.Game(":chicken: Happy Easter!"))
			
		elif (now.month == 2 and now.day in range(8, 12)) or (now.month == 11 and now.day in range(12, 22)):
			await self.update_avatar(self.bot, "media/avatars/trans.jpg", last)
			await self.bot.change_presence(activity = discord.Game(":transgender_flag: Trans Rights!"))
			
		else:
			await self.update_avatar(self.bot, "media/avatars/generic.jpg", last)
			await self.bot.change_presence(activity = random.choice(BotTasks.STATUSES))
	
	@staticmethod		
	async def update_avatar(bot, path, last):
		if last == path: return
		
		with open(path, "rb") as image:
			data = bytearray(image.read())
		
		await bot.user.edit(avatar = data)
		await bot.dbc.store_set("last_avatar", path)
		
	def write_book(self, doc):
		#don't judge me, I didn't make the choice to store the info in a Word doc
		with open("data/book/book.docx", "wb") as file:
			file.seek(0)
			file.write(doc.getvalue())
			file.truncate()
			
		text = re.sub(self.STRIP_SPACES, "\n", docx2python("data/book/book.docx").text)
		results = re.findall(self.FIND_DATA, text[text.find("This document contains"):])
		return { entry[0]: entry for entry in results }
		
	@tasks.loop(hours = 10)
	async def sync_book(self):
		response = await utils.get_json(
			self.bot.session,
			f"https://www.googleapis.com/drive/v3/files/1RyuY_WM4zSRtVhTwjs9lut9vrlMmmd24?"
			f"fields=modifiedTime%2C%20webContentLink&key={self.bot.conf['GCS_TOKEN']}"
		)
		timestamp = time.mktime(datetime.fromisoformat(response["modifiedTime"].rsplit(".")[0]).timetuple())
		
		if timestamp <= int(await self.bot.dbc.store_get("book_timestamp")): 
			return
		
		doc = await utils.get_bytes(self.bot.session, response["webContentLink"])
		book = await self.bot.loop.run_in_executor(None, self.write_book, doc)
		
		await self.bot.dbc.execute(
			f"DELETE FROM armigers WHERE greii_n NOT IN ({','.join(['?'] * len(book))})",
			tuple(book.keys())
		)
		await self.bot.dbc.commit()
		
		for greii_n, entry in book.items():
			has_id = await self.bot.dbc.execute(
				"SELECT * FROM armigers WHERE discord_id IS NULL AND greii_n IS ?",
				(greii_n,)
			)
			
			await self.bot.dbc.execute(
				"INSERT INTO armigers (greii_n, qualified_name, qualified_id, blazon) VALUES"
				" (?, ?, ?, ?) ON CONFLICT(greii_n) DO UPDATE SET qualified_name = ?, qualified_id = ?, blazon = ?;",
				(greii_n, entry[1], entry[2], entry[3], entry[1], entry[2], entry[3])
			)
			
			if has_id:
				user = await utils.unqualify_name(self.bot, entry[1], entry[2])
				await self.bot.dbc.execute(
					"UPDATE armigers SET discord_id = ? WHERE greii_n = ?;",
					(user.id if user else None, greii_n)
				)
			
			await self.bot.dbc.commit()
			
		await self.bot.dbc.store_set("book_timestamp", f"{timestamp:.0f}")
		self.bot.logger.info(f"Successfully refreshed armiger database.")
		
	@tasks.loop(hours = 2)
	async def get_reddit_posts(self):
		bot = self.bot

		async for feed in await self.bot.dbc.execute("SELECT * FROM reddit_feeds"):
			query = urllib.parse.quote(feed[5])
			posts = await utils.get_json(
				self.bot.session,
				f"https://www.reddit.com/r/{feed[3]}/search.json?q={query}&restrict_sr=on&sort=new&limit=8"
			)
			
			if posts.get("error"): 
				bot.logger.warning(f"Cannot access Reddit:\n{posts}")
				continue #necessary as reddit can be down
			
			posts = posts["data"]["children"]
			channel = await utils.get_channel(self.bot, feed[2])
			
			if len(posts) == 0: continue
			
			for post in posts:
				post = post["data"]
				if post["name"] == feed[6]: break
				
				desc = "" if not post.get("selftext") else post["selftext"].split("\n#")[0]
				
				embed = embeds.FEED.create(post["title"], desc)
				embed.url = f"https://old.reddit.com{post['permalink']}"
				embed.set_footer(text = f"posted to r/{post['subreddit']} by u/{post['author']}")
				
				if post.get("preview"):
					embed.set_thumbnail(url = post["preview"]["images"][0]["source"]["url"].replace("&amp;","&"))
				
				await channel.send(None if not bool(feed[4]) else "@everyone", embed = embed)
			
			if posts[0]["data"]["name"] != feed[6]:	
				await bot.dbc.execute(
					"UPDATE reddit_feeds SET last_post = ? WHERE id = ?", 
					(posts[0]["data"]["name"], feed[0])
				)
				await bot.dbc.commit()
				
		bot.logger.info(f"Successfully fetched Reddit posts.")
	
	@update_info.before_loop
	@sync_book.before_loop			
	@get_reddit_posts.before_loop
	async def wait_before_loop(self):
		await self.bot.wait_until_ready()
		
def setup(bot):
	bot.add_cog(BotTasks(bot))