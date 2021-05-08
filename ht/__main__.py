import discord, aiosqlite, aiohttp, logging, json, os
from discord.ext import commands
from . import utils

class Heraldtron(commands.Bot):
	DEFAULT_COGS = [
		"errors", "events", "modtools", "heraldry", 
		"misc", "tasks", "vexillology", "meta"
	]
	
	REQUISITES = [
		"DISCORD_TOKEN", "GCS_TOKEN", "GCS_CX", "AR_RIJKS", 
		"AR_EURO", "AR_DGTNZ", "AR_SMTHS", "AR_DDBTK", "DEEP_AI",
		"DB_PATH"
	]
	
	def __init__(self, *args, **kwargs):
		self.conf = self.load_conf()
		logging.basicConfig(level = self.conf.get("LOG_LEVEL") or 20)
		
		super().__init__(
			command_prefix = "!",
			description = "A heraldry-related bot designed for the Heraldry Community.",
			activity = discord.Game("a !challenge"),
			intents = self.get_default_intents(),
			max_messages = 12000,
			*args, 
			**kwargs
		)
		
		self.session = self.loop.run_until_complete(self.start_session())
		self.dbc = self.loop.run_until_complete(aiosqlite.connect(self.conf["DB_PATH"]))
		
		if self.conf.get("OWNER_ONLY"):
			self.add_check(utils.check_is_owner)
		
	def get_default_intents(self):
		return discord.Intents(
			guilds = True,
			members = True,
			messages = True,
			reactions = True
		)
		
	def load_conf(self):
		with open("config.json") as file:
			try: conf = json.load(file)
			except: raise FileNotFoundError("Cannot load JSON file.")
			
		if not all(r in conf for r in self.REQUISITES):
			raise NameError("JSON file does not have required values.")
				
		return conf
		
	def load_default_cogs(self, custom_list = None):
		coglist = custom_list or self.DEFAULT_COGS
		
		for cog in coglist:
			self.load_extension(f"ht.cogs.{cog}")
			print(f"Cog {cog} loaded sucessfully")
			
		if self.conf.get("USE_JISHAKU"):
			os.environ["JISHAKU_HIDE"] = "1" 
			self.load_extension("jishaku")
			coglist.append("jishaku")
			
		return coglist
		
	async def start_session(self):
		return aiohttp.ClientSession(loop=self.loop)
		
	async def close(self):
		await self.dbc.close()
		await self.session.close()
		await super().close()

if __name__ == "__main__":
	bot = Heraldtron()
	bot.load_default_cogs()
	bot.run(bot.conf["DISCORD_TOKEN"])