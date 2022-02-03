import discord, asyncio, aiohttp, logging, json, os, time
from discord.ext import commands
from collections import defaultdict
from . import db, utils

class Heraldtron(commands.Bot):
	DEFAULT_COGS = [
		"errors", "events", "modsettings",  "modtools", 
		"heraldry", "misc", "reference", "resource", "roll", 
		"rollchannels", "tasks", "vexillology", "meta"
	]
	
	REQUISITES = [
		"DISCORD_TOKEN", "GCS_TOKEN"
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
		self.melded_cogs = defaultdict(list)
		
		super().__init__(
			command_prefix = "!", #kept for documentation
			description = "A heraldry-related bot designed for the Heraldry Community.",
			intents = self.get_default_intents(),
			max_messages = 12000,
			case_insensitive = True,
			*args, 
			**kwargs
		)
		
		self.session = self.loop.run_until_complete(self.start_session())
		self.dbc = self.loop.run_until_complete(self.setup_db())
		
		self.ready_flag = asyncio.Event()
		self.loop.create_task(self.refresh_cache())
		self.active_dms = set()
		
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
			self.load_extension("ht.cogs.debug")
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
		dbc = await db.connect(self.conf["DB_PATH"])
		count = await dbc.execute_fetchone("SELECT COUNT(*) FROM sqlite_master")
		
		if count[0] == 0:
			with open("data/db/schema.sql", "r") as file:
				await dbc.executescript(file.read())
			await dbc.commit()
			
		return dbc
		
	async def refresh_cache_guild(self, guild_id):
		record = await self.dbc.execute_fetchone(
			"SELECT * FROM guilds WHERE discord_id = ?", (guild_id,)
		)
		guild = await utils.get_guild(self, record[0])
		
		if not guild or not record: return
		self.guild_cache[guild_id] = (guild, record)
		
	async def refresh_cache(self):
		await self.wait_until_ready()
		self.reset_cache()

		async for record in await self.dbc.execute("SELECT * FROM guilds"):
			guild = await utils.get_guild(self, record[0])
			
			if not guild or not record: continue
			self.guild_cache[record[0]] = (guild, record)
			
		async for proposal in await self.dbc.execute("SELECT * FROM proposal_channels"):
			self.proposal_cache.add(proposal[0])
		
		self.ready_flag.set()	
		
	def add_cog(self, cog):
		super().add_cog(cog)
		if isinstance(cog, utils.MeldedCog):
			self.melded_cogs[cog.category].append(cog)
			
	def remove_cog(self, cog):
		super().remove_cog(cog)
		if isinstance(cog, utils.MeldedCog):
			self.melded_cogs[cog.category].remove(cog)
		
	async def get_prefix(self, message):
		list = (self.command_prefix, f"<@{bot.user.id}> ", f"<@!{bot.user.id}> ")
		
		if not message.guild and message.channel.id not in self.active_dms:
			return (*list, "")
			
		return list
		
	def reset_cache(self):
		self.ready_flag.clear()
		self.guild_cache = {}
		self.proposal_cache = set()
		
	async def on_message(self, message):
		await self.ready_flag.wait()
		await self.process_commands(message)
		
	async def close(self):
		self.reset_cache()
		await self.dbc.close()
		await self.session.close()
		await super().close()

if __name__ == "__main__":
	start = time.perf_counter()
	bot = Heraldtron()
	
	bot.load_default_cogs()
	bot.log_time(start)
	bot.run(bot.conf["DISCORD_TOKEN"])
