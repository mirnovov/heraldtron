import discord, aiohttp, traceback, logging, json, time
from discord.ext import commands
from .. import utils

class BotErrors(commands.Cog, name = "Bot Errors"):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		ctx.handled = False
		
		if not isinstance(error, commands.CommandInvokeError):
			if isinstance(error, commands.CommandNotFound):
				phrase = ctx.message.content
				
				if(phrase.startswith("!!") or phrase.startswith("!?")):
					return #ignore "!!!" etc
				
				await self.warn(ctx, "Command not found",
					"The command you entered does not exist. Check your spelling and try again."
				)
				
			elif isinstance(error, commands.NoPrivateMessage):
				await self.warn(ctx, "Command must be public",
					"The command you entered cannot be used during direct messaging."
				)
				
			elif isinstance(error, commands.MissingRole):
				await self.warn(ctx, "Command requires elevated privileges",
					"The command you entered requires a role that you do not possess."
				)
				
			elif isinstance(error, commands.MissingRequiredArgument):
				await self.warn(ctx, "Command is missing argument",
					f"The command you entered requires you to enter `{error.param.name}`."\
					" Check that it is entered correctly and try again."
				)
				
			elif isinstance(error, commands.UserNotFound):
				await self.warn(ctx, "Command could not locate user",
					"The command you entered requires a valid user. Check that their name"\
					" is mentioned correctly and try again."
				)
				
			elif isinstance(error, commands.TooManyArguments):
				await self.warn(ctx, "Command given too many arguments",
					"The command you entered does not accept this many arguments."\
					" Check that you are using it correctly and try again."
				)
						  
			elif isinstance(error, commands.NotOwner):
				await self.warn(ctx, "Command requires elevated privileges",
					"The command you entered is solely permitted to be used by the bot owner."
				)
			
		if not ctx.handled:
			owner = (await self.bot.application_info()).owner
			
			if isinstance(error, commands.CommandInvokeError):
				error = error.original
				
			if isinstance(error, aiohttp.ClientConnectionError):
				await self.warn(ctx, "Could not connect to server",
					"The server that the bot is trying to reach cannot connect. An error report has been sent."\
					f" If the problem persists, contact {owner.mention}.", error
				)
			elif isinstance(error, json.JSONDecodeError) or isinstance(error, aiohttp.ContentTypeError):
				await self.warn(ctx, "Could not decode server response",
					"The server has returned undecodable content. An error report has been sent."\
					f" If the problem persists, contact {owner.mention}.", error
				)
			else:
				await self.warn(ctx, "Unknown error",
					"Heraldtron has encountered an unforseen difficulty. An error report has been sent.",
					error
				)
		
	async def warn(self, ctx, title, message, error = None):
		await ctx.send(embed = utils.nv_embed(title, message))
		if error:
			logging.getLogger("heraldtron").warning(
				f"{type(error).__name__}: {str(error)}\n {''.join(traceback.format_tb(error.__traceback__))}"\
				f"(Error reported as '{title}: {message}')"
			)
		ctx.handled = True
			
def setup(bot):
	bot.add_cog(BotErrors(bot))