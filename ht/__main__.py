import discord, aiosqlite, aiohttp, logging, json, os, time
from discord.ext import commands
from . import utils

class Heraldtron(commands.Bot):
	DEFAULT_COGS = [
		"errors", "events", "modtools", "heraldry", 
		"misc", "sort", "tasks", "vexillology", "meta"
	]
	
	REQUISITES = [
		"DISCORD_TOKEN", "GCS_TOKEN", "GCS_CX", "AR_RIJKS", 
		"AR_EURO", "AR_DGTNZ", "AR_SMTHS", "AR_DDBTK", "DEEP_AI"
	]
	
	DEFAULT_CONF = {
		"DB_PATH": "./data/db/heraldtron.db",
		"LOG_LEVEL": 20,
		"OWNER_ONLY": False,
		"USE_JISHAKU": False
	}
	
	def __init__(self, *args, **kwargs):
		self.conf = self.load_conf()
		self.root_logger = self.setup_root_logger() 
		self.logger = logging.getLogger("heraldtron")
		
		super().__init__(
			command_prefix = "!", #kept for documentation
			description = "A heraldry-related bot designed for the Heraldry Community.",
			activity = discord.Game("a !challenge"),
			intents = self.get_default_intents(),
			max_messages = 12000,
			*args, 
			**kwargs
		)
		
		self.session = self.loop.run_until_complete(self.start_session())
		self.dbc = self.loop.run_until_complete(self.setup_db())
		
		self.loop.create_task(self.refresh_cache())
		
		if self.conf["OWNER_ONLY"]:
			self.add_check(utils.check_is_owner)
			
		with open("media/ascii_art", "r") as file:
			ascii = f"\n{file.read()}"
			
		self.logger.info(f"Bot initialisation complete. {ascii}")
		
	def get_default_intents(self):
		return discord.Intents(
			guilds = True,
			members = True,
			messages = True,
			reactions = True,
			presences = True
		)
		
	def load_conf(self):
		with open("config.json") as file:
			try: conf = json.load(file)
			except: raise FileNotFoundError("Cannot load JSON file.")
			
		if not all(r in conf for r in Heraldtron.REQUISITES):
			raise NameError("JSON file does not have required values.")
				
		return dict(Heraldtron.DEFAULT_CONF, **conf)
		
	def load_default_cogs(self, custom_list = None):
		coglist = custom_list or Heraldtron.DEFAULT_COGS
		
		for cog in coglist:
			self.load_extension(f"ht.cogs.{cog}")
			self.logger.info(f"Cog \"{cog}\" loaded successfully")
			
		if self.conf.get("USE_JISHAKU"):
			os.environ["JISHAKU_HIDE"] = "1" 
			self.load_extension("jishaku")
			coglist.append("jishaku")
			
		return coglist
		
	def setup_root_logger(self):
		logger = logging.getLogger()
		logger.setLevel(self.conf["LOG_LEVEL"])
		
		handler = logging.StreamHandler()
		handler.setFormatter(utils.NvFormatter())
		logger.addHandler(handler)
		
		return logger
		
	def log_time(self, start):
		self.logger.info(f"Startup time: {time.perf_counter() - start:.3f}s")
		
	async def start_session(self):
		return aiohttp.ClientSession(
			loop = self.loop, headers = {"User-Agent": utils.USER_AGENT}
		)
		
	async def setup_db(self):
		dbc = await aiosqlite.connect(self.conf["DB_PATH"])
		count = await utils.fetchone(dbc, "SELECT COUNT(*) FROM sqlite_master")
		
		if count[0] == 0:
			with open("data/db/schema.sql", "r") as file:
				await dbc.executescript(file.read())
			await dbc.commit()
			
		return dbc
		
	async def refresh_cache_guild(self, guild_id):
		record = await utils.fetchone(
			self.dbc, "SELECT * FROM guilds WHERE discord_id = ?", (guild_id,)
		)
		guild = await utils.get_guild(self, record[0])
		
		if not guild or not record: return
		self.guild_cache[guild_id] = (guild, record)
			
	async def refresh_cache(self):
		await self.wait_until_ready()
		self.guild_cache = {}
		
		async for record in await self.dbc.execute("SELECT * FROM guilds"):
			guild = await utils.get_guild(self, record[0])
			
			if not guild or not record: continue
			self.guild_cache[record[0]] = (guild, record)
		
	async def get_prefix(self, message):
		list = (self.command_prefix, f"<@{bot.user.id}> ", f"<@!{bot.user.id}> ")
		
		if not message.guild:
			return (*list, "")
			
		return list
		
	async def close(self):
		await self.dbc.close()
		await self.session.close()
		await super().close()

if __name__ == "__main__":
	start = time.perf_counter()
	bot = Heraldtron()
	
	bot.load_default_cogs()
	bot.log_time(start)
	bot.run(bot.conf["DISCORD_TOKEN"])