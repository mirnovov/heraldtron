import discord, hashlib, urllib, time, re, random, os
from docx2python import docx2python
from datetime import datetime, timezone
from discord.ext import commands, tasks
from .. import utils, embeds

class BotTasks(commands.Cog, name = "Bot tasks"):
	STRIP_SPACES = re.compile(r"\n[\t\s]+")
	FIND_DATA = re.compile(r"GreiiN:(\d+) - ([^\n]+)[\s\S]+?(Blazon[\s\S]+?)(?=GreiiN|$)")

	def __init__(self, bot):
		self.bot = bot
		self.update_info.start()
		self.sync_book.start()

		if not os.path.isdir("data/book"):
			os.mkdir("data/book")

	def cog_unload(self):
		self.update_info.stop()
		self.sync_book.stop()

	@tasks.loop(hours = 12)
	async def update_info(self, force = False):
		now = datetime.now().date()
		last = "" if force else await self.bot.dbc.store_get("last_avatar")

		if now.month == 6 and now.day in range(8, 12):
			await self.update_avatar(self.bot, "media/avatars/ihd.png", last)
			await self.bot.change_presence(activity = discord.Game("\U0001F6E1\uFE0F International Heraldry Day"))

		elif now.month == 6:
			await self.update_avatar(self.bot, "media/avatars/pride.png", last)
			await self.bot.change_presence(activity = discord.Game("\U0001F3F3\uFE0F\u200D\U0001F308 Happy Pride Month!"))

		elif now.month == 12:
			await self.update_avatar(self.bot, "media/avatars/holiday.png", last)
			await self.bot.change_presence(activity = discord.Game("\U0001F384 Happy Holidays!"))

		elif now.month == 4:
			await self.update_avatar(self.bot, "media/avatars/easter.png", last)
			await self.bot.change_presence(activity = discord.Game("\U0001F414 Happy Easter!"))

		elif (now.month == 2 and now.day in range(8, 12)) or (now.month == 11 and now.day in range(12, 22)):
			await self.update_avatar(self.bot, "media/avatars/trans.png", last)
			await self.bot.change_presence(activity = discord.Game("\U0001F3F3\uFE0F\u200D\u26A7\uFE0F Trans Rights!"))

		else:
			await self.update_avatar(self.bot, "media/avatars/generic.png", last)
			await self.bot.change_presence(activity = discord.Game("with /slash commands"))

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
		entries = []
		
		for entry in results:
			hasher = hashlib.md5()
			
			for hash_data in entry[1:3]:
				hasher.update(hash_data.encode())

			entries.append((
				int(entry[0]), entry[1], entry[2], hasher.hexdigest()
			))	
				
		return entries	
		
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
			tuple(a[0] for a in book)
		)
		await self.bot.dbc.commit()
		
		for greii_n, username, blazon, book_hash in book:
			data = await self.bot.dbc.execute_fetchone(
				"SELECT book_hash, discord_id FROM armigers WHERE greii_n = ?;", (greii_n,)
			)
			
			# GreiiN not recorded
			if data == None:
				await self.bot.dbc.execute(
					"INSERT INTO armigers (greii_n, qualified_name, blazon, book_hash) VALUES (?1, ?2, ?3, ?4)",
					(greii_n, username, blazon, book_hash)
				)
			
			# GreiiN data needs update
			elif book_hash != data["book_hash"]:
				if "#" in username and data["discord_id"]: 
					user = discord.utils.get(self.bot.users, id = int(data["discord_id"]))
					if user: username = user.name
		
				await self.bot.dbc.execute(
					"UPDATE armigers SET qualified_name = ?2, blazon = ?3, book_hash = ?4 WHERE greii_n = ?1;",
					(greii_n, username, blazon, book_hash)
				)
				
			# GreiiN data doesn't have Discord ID linked
			if data and not data["discord_id"]:
				user = discord.utils.get(self.bot.users, name = username)
				if user:
					await self.bot.dbc.execute(
						"UPDATE armigers SET discord_id = ?1 WHERE greii_n = ?2;",
						(user.id, greii_n)
					)

			await self.bot.dbc.commit()

		await self.bot.dbc.store_set("book_timestamp", f"{timestamp:.0f}")
		self.bot.logger.info(f"Successfully refreshed armiger database.")

	@update_info.before_loop
	@sync_book.before_loop
	async def wait_before_loop(self):
		await self.bot.wait_until_ready()

async def setup(bot):
	await bot.add_cog(BotTasks(bot))
