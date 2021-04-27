import discord, aiosqlite, aiohttp, logging, json, os, traceback
from discord.ext import commands
from . import utils

class NvBot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(
			command_prefix = "!",
			description = "A heraldry-related bot designed for the Heraldry Community.",
			activity = discord.Game("a !challenge"),
			intents = self.get_default_intents(),
			max_messages = 12000,
			*args, 
			**kwargs
		)
		
		self.conf = self.load_conf()
		self.dbc = self.loop.run_until_complete(aiosqlite.connect(self.conf["DB_PATH"]))
		self.session = aiohttp.ClientSession(loop=self.loop)
		
		if self.conf["OWNER_ONLY"]:
			self.add_check(utils.check_is_owner)
		
	def get_default_intents(self):
		intents = discord.Intents.default()
		intents.typing = False
		intents.webhooks = False
		intents.integrations = False
		intents.invites = False
		intents.members = True

		return intents
		
	def load_conf(self):
		with open("config.json") as file:
			try: conf = json.load(file)
			except: raise FileNotFoundError("Cannot load JSON file.")
			
		requisites = [
			"DISCORD_TOKEN", "GCS_TOKEN", "GCS_CX", "AR_RIJKS", 
			"AR_EURO", "AR_DGTNZ", "AR_SMTHS", "AR_DDBTK", "DEEP_AI",
			"DB_PATH"
		]
		
		for r in requisites:
			if r not in conf:
				raise NameError("JSON file does not have required values.")
				
		return conf
		
	def load_default_cogs(self, custom_list = None):
		coglist = custom_list or ["events", "modtools", "heraldry", "misc", "vexillology", "meta"]
		
		for cog in coglist:
			self.load_extension(f"ht.cogs.{cog}")
			print(f"Cog {cog} loaded sucessfully")
			
		if self.conf.get("USE_JISHAKU"):
			os.environ["JISHAKU_HIDE"] = "1" 
			self.load_extension("jishaku")
			coglist.append("jishaku")
			
		return coglist
		
	async def close(self):
		await self.dbc.close()
		await self.session.close()
		await super().close()
		
	async def on_command_error(self, ctx, error):
		title = message = ""
		
		if isinstance(error, commands.CommandNotFound):
			phrase = ctx.message.content
			
			if(phrase.startswith("!!") or phrase.startswith("!?")):
				return #ignore "!!!" etc
			
			title = "Command not found"
			message = "The command you entered does not exist. Check your spelling and try again."
			
		elif isinstance(error, commands.NoPrivateMessage):
			title = "Command must be public"
			message = "The command you entered cannot be used during direct messaging."
			
		elif isinstance(error, commands.MissingRole):
			title = "Command requires elevated privileges"
			message = "The command you entered requires a role that you do not possess."
			
		elif isinstance(error, commands.MissingRequiredArgument):
			title = "Command is missing argument"
			message = f"The command you entered requires the *{error.param.name}* argument."\
					  " Check that it is entered correctly and try again."
			
		elif isinstance(error, commands.UserNotFound):
			title = "Command could not locate user"
			message = f"The command you entered requires a valid user."\
					  " Check that their name is mentioned correctly and try again."
			
		elif isinstance(error, commands.TooManyArguments):
			title = "Command given too many arguments"
			message = f"The command you entered does not accept this many arguments."\
					  " Check that you are using it correctly and try again."
					  
		elif isinstance(error, commands.NotOwner):
			title = "Command requires elevated privileges"
			message = f"The command you entered is solely permitted to be used by the bot owner."
			
		else:
			cause = error if not isinstance(error, commands.CommandInvokeError) else error.original
			trace = "".join(traceback.format_tb(cause.__traceback__))
			app_info = await self.application_info()
			dm = await app_info.owner.create_dm()	
			
			if not isinstance(ctx.channel, discord.abc.GuildChannel) and not self.is_owner(ctx.author):
				title = "Unknown error"
				message = f"Heraldtron has encountered an unforseen difficulty. An error report has been sent."
			
			await dm.send(embed = utils.nv_embed(
				"Unknown error",
				f"Heraldtron has encountered an unforseen difficulty due to a [command]({ctx.message.jump_url}).\n\n"\
				f"**Error Info**:\n```python\n{type(cause).__name__}: {str(cause)}\n```\n"
				f"**Stack Trace**:\n```python\n{trace}\n```"
			))
		
		if title and message:
			await ctx.send(embed = utils.nv_embed(title, message))

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	bot = NvBot()
	bot.load_default_cogs()
	bot.run(bot.conf["DISCORD_TOKEN"])