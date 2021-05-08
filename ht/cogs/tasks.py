import discord, sqlite3, urllib, logging, time, re, os
from docx2python import docx2python
from datetime import datetime
from discord.ext import commands, tasks
from .. import utils, embeds

class BotTasks(commands.Cog, name = "Bot tasks"):
	STRIP_SPACES = re.compile(r"\n[\t\s]+")
	FIND_DATA = re.compile(r"GreiiN:(\d+) - (?:[^\n\r#]+\n)?(.+)#(\d+)[\s\S]+?(Blazon[\s\S]+?)(?=GreiiN|$)")
	
	def __init__(self, bot):
		self.bot = bot
		self.get_reddit_posts.start()
		self.sync_book.start()
		
		if not os.path.isdir("data/temp"):
			os.mkdir("data/temp")
			
		if not os.path.isfile("data/temp/book_timestamp"):
			with open("data/temp/book_timestamp","w") as file:
				file.write("0")
		
	def cog_unload(self):
		self.get_reddit_posts.stop()
		self.sync_book.stop()
		
	def write_book(self, doc):
		#don't judge me, I didn't make the choice to store the info in a Word doc
		with open("data/temp/book.docx", "wb") as file:
			file.seek(0)
			file.write(doc.getvalue())
			file.truncate()
			
		text = re.sub(self.STRIP_SPACES, "\n", docx2python("data/temp/book.docx").text)
		results = re.findall(self.FIND_DATA, text[text.find("This document contains"):])
		return { entry[0]: entry for entry in results }
		
	@tasks.loop(hours = 10)
	async def sync_book(self):
		response = await utils.get_json(
			self.bot.session,
			f"https://www.googleapis.com/drive/v3/files/1RyuY_WM4zSRtVhTwjs9lut9vrlMmmd24?"\
			f"fields=modifiedTime%2C%20webContentLink&key={self.bot.conf['GCS_TOKEN']}"
		)
		timestamp = time.mktime(datetime.fromisoformat(response["modifiedTime"].rsplit(".")[0]).timetuple())
		
		with open("data/temp/book_timestamp", "r") as file:
			if timestamp <= int(file.read()): return
		
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
				"INSERT INTO armigers (greii_n, qualified_name, qualified_id, blazon) VALUES"\
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
			
		with open("data/temp/book_timestamp", "w") as file:
			file.seek(0)
			file.write(f"{timestamp:.0f}")
			file.truncate()
			
		logging.getLogger("heraldtron").info(f"Successfully refreshed armiger database.")
		
	@tasks.loop(hours = 2)
	async def get_reddit_posts(self):
		bot = self.bot

		async for feed in await self.bot.dbc.execute("SELECT * FROM reddit_feeds"):
			query = urllib.parse.quote(feed[4])
			posts = await utils.get_json(
				self.bot.session,
				f"https://www.reddit.com/r/{feed[3]}/search.json?q={query}&restrict_sr=on&sort=new&limit=8"
			)
			
			if posts.get("error"): 
				logging.getLogger("heraldtron").warning(f"Cannot access Reddit:\n{posts}")
				continue #necessary as reddit can be down
			
			posts = posts["data"]["children"]
			channel = await utils.get_channel(self.bot, feed[2])
			
			if len(posts) == 0: continue
			
			for post in posts:
				post = post["data"]
				if post["name"] == feed[5]: break
				
				desc = "" if not post.get("selftext") else post["selftext"].split("\n#")[0]
				
				embed = embeds.FEED.create(post["title"], desc)
				embed.url = f"https://old.reddit.com{post['permalink']}"
				embed.set_footer(text = f"posted to r/{post['subreddit']} by u/{post['author']}")
				
				if post.get("preview"):
					embed.set_thumbnail(url = post["preview"]["images"][0]["source"]["url"].replace("&amp;","&"))
				
				await channel.send(embed = embed)
			
			if posts[0]["data"]["name"] != feed[5]:	
				await bot.dbc.execute(
					"UPDATE reddit_feeds SET last_post = ? WHERE id = ?", 
					(posts[0]["data"]["name"], feed[0])
				)
				await bot.dbc.commit()
				
		logging.getLogger("heraldtron").info(f"Successfully fetched Reddit posts.")
	
	@sync_book.before_loop			
	@get_reddit_posts.before_loop
	async def wait_before_loop(self):
		await self.bot.wait_until_ready()
		
def setup(bot):
	bot.add_cog(BotTasks(bot))