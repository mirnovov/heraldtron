import discord, asyncio, aiohttp, json, logging, os, sys, time, traceback
from discord.ext import commands
from collections import defaultdict
from . import db, utils

class Heraldtron(commands.Bot):
	DEFAULT_COGS = [
		"debug", "errors", "events_guild", "events_member", "modsettings",  
		"modtools", "heraldry", "misc", "reference", "resource", 
		"roll", "rollchannels", "tasks", "vexillology", "meta"
	]

	REQUISITES = [
		"DISCORD_TOKEN", "GCS_TOKEN"
	]

	DEFAULT_CONF = {
		"DB_PATH": "./data/db/heraldtron.db",
		"LOG_LEVEL": 20,
		"OWNER_ONLY": False,
		"PREFIX": "!"
	}

	HERALDRY_GUILD = 272117928298676225

	def __init__(self, *args, **kwargs):
		self.conf = self.load_conf()
		self.setup_logging()
				
		self.melded_cogs = defaultdict(list)
		self.active_dms = set()
		
		self.ready_flag = asyncio.Event()
		self.session = aiohttp.ClientSession(
			headers = {"User-Agent": utils.USER_AGENT}
		) 
		
		self.reset_cache()	
		
		if self.conf["OWNER_ONLY"]:
			self.add_check(utils.check_is_owner)

		super().__init__(
			command_prefix = self.conf["PREFIX"], #kept for documentation
			description = "A heraldry-related bot designed for the Heraldry Community.",
			intents = discord.Intents(
				guilds = True, members = True, messages = True,
				reactions = True, presences = True, message_content = True
			),
			max_messages = 12000,
			case_insensitive = True,
			*args,
			**kwargs
		)
		
		with open("media/ascii_art", "r") as file:
			self.logger.info(f"Bot initialisation complete.\n{file.read()}")
		
	def load_conf(self):
		with open("config.json") as file:
			try: conf = json.load(file)
			except: raise FileNotFoundError("Cannot load JSON file.")
		
		if not all(r in conf for r in Heraldtron.REQUISITES):
			raise NameError("JSON file does not have required values.")
		
		return dict(Heraldtron.DEFAULT_CONF, **conf)
		
	def setup_logging(self):
		self.default_logger = logging.getLogger()
		self.dpy_logger = logging.getLogger("discord")
		self.logger = logging.getLogger("heraldtron")

		level = self.conf["LOG_LEVEL"]
		
		self.default_logger.setLevel(level)
		self.dpy_logger.setLevel(level)
		
		handler = logging.StreamHandler()
		handler.setFormatter(utils.NvFormatter())
		self.default_logger.addHandler(handler)
		
	def reset_cache(self):
		self.ready_flag.clear()
		self.guild_cache = {}
		self.channel_cache = {}
		self.proposal_cache = {}
		
	async def load_default_cogs(self, custom_list = None):
		coglist = custom_list or Heraldtron.DEFAULT_COGS

		for cog in coglist:
			await self.load_extension(f"ht.cogs.{cog}")
			self.logger.info(f"Cog \"{cog}\" loaded successfully")

		return coglist

	async def setup_db(self):
		self.dbc = await db.connect(self.conf["DB_PATH"])
		count = await self.dbc.execute_fetchone("SELECT COUNT(*) FROM sqlite_master")

		if count[0] == 0:
			with open("data/db/schema.sql", "r") as file:
				await dbc.executescript(file.read())
			await self.dbc.commit()

	async def refresh_cache_guild(self, guild_id):
		record = await self.dbc.execute_fetchone(
			"SELECT * FROM guilds WHERE discord_id = ?", (guild_id,)
		)
		guild = await utils.get_guild(self, record[0])

		if not guild or not record: return
		self.guild_cache[guild_id] = (guild, record)

	async def refresh_cache(self):
		await self.wait_until_ready()

		async for record in await self.dbc.execute("SELECT * FROM guilds"):
			guild = await utils.get_guild(self, record[0])

			if not guild or not record: continue
			self.guild_cache[record[0]] = (guild, record)

		async for record in await self.dbc.execute("SELECT * FROM channels"):
			self.channel_cache[record[0]] = record

			if not record[2]: continue
			channel = await utils.get_channel(self, record[0])

			async for message in channel.history():
				if not message.flags.has_thread: continue
				self.proposal_cache[message.id] = (message, time.time())

		self.ready_flag.set()
		self.logger.info("Successfully cached data.")

	async def add_cog(self, cog):
		await super().add_cog(cog)
		if isinstance(cog, utils.MeldedCog):
			self.melded_cogs[cog.category].append(cog)

	async def remove_cog(self, cog):
		await super().remove_cog(cog)
		if isinstance(cog, utils.MeldedCog):
			self.melded_cogs[cog.category].remove(cog)

	async def get_prefix(self, message):
		list = (self.command_prefix, f"<@{self.user.id}> ", f"<@!{self.user.id}> ")

		if not message.guild and message.channel.id not in self.active_dms:
			return (*list, "")

		return list
		
	async def on_error(self, *args, **kwargs):
		error = sys.exc_info()
		self.dpy_logger.error(
			f"{error[0].__name__}: {error[1]}\n {''.join(traceback.format_tb(error[2]))}"
		)

	async def on_message(self, message):
		await self.ready_flag.wait()
		await self.process_commands(message)

	async def close(self):
		self.reset_cache()
		await self.dbc.close()
		await self.session.close()
		await super().close()
		
async def main():
	start = time.perf_counter()

	async with Heraldtron() as bot:
		await bot.setup_db()
		await bot.load_default_cogs()
		
		bot.loop.create_task(bot.refresh_cache())
		bot.logger.info(f"Startup time: {time.perf_counter() - start:.3f}s")

		await bot.start(bot.conf["DISCORD_TOKEN"])

if __name__ == "__main__":
	asyncio.run(main())
