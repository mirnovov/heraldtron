import discord, aiohttp, traceback, logging, json, re, sys
from discord.ext import commands
from .. import views, utils

class BotErrors(commands.Cog, name = "Bot Errors"):
	IGNORE_PAT = re.compile(r"!(!|\?)") #ignore "!!!" etc

	def __init__(self, bot):
		self.bot = bot
		self.bot.tree.on_error = self.on_app_command_error
	
	async def respond_to_error(self, error, mention):
		warn = False
		
		match type(error):
			case commands.DisabledCommand | commands.CommandNotFound:
				title = "Command not found"
				description = "The command you entered does not exist. Check your spelling and try again."
				
			case commands.NoPrivateMessage:
				title = "Command must be public"
				description = "The command you entered cannot be used during direct messaging."
				
			case commands.MissingRole:
				title = "Command requires elevated privileges"
				description = "The command you entered requires a role that you do not possess."
				
			case commands.MissingRequiredArgument:
				title = "Command is missing argument"
				description = f"The command you entered requires you to enter `{error.param.name}`. Check that it is entered correctly and try again."
				
			case commands.MissingRequiredAttachment:
				title = "Command is missing image"
				description = f"The command you entered requires you to attach an image. Attach an image and try again."
				
			case commands.UserNotFound:
				title = "Command could not locate user"
				description = "The command you entered requires a valid user. Check that their name is mentioned correctly and try again."
				
			case commands.TooManyArguments:
				title = "Command given too many arguments"
				description = "The command you entered does not accept this many arguments. Check that you are using it correctly and try again."
				
			case commands.NotOwner:
				title = "Command requires elevated privileges"
				description = "The command you entered is solely permitted to be used by the bot owner."
				
			case commands.BadArgument:
				title = "Command given invalid argument"
				description = "One or more of the arguments you entered is invalid. Check that the command is correct and try again."
				
			case aiohttp.ClientConnectionError:
				warn = True
				title = "Could not connect to server"
				description = "The server that the bot is trying to reach cannot connect. An error report has been sent."\
									f" If the problem persists, contact {mention}."
				
			case json.JSONDecodeError:
				warn = True
				title = "Could not decode server response"
				description = "The server has returned undecodable content. An error report has been sent."\
								  	f" If the problem persists, contact {mention}."
				
			case aiohttp.ContentTypeError:
				warn = True
				title = "Could not decode server response"
				description = "The server has returned content of the incorrect type. An error report has been sent."\
								  	f" If the problem persists, contact {mention}."
									  
			case discord.Forbidden:
				warn = True
				title = "Permission error"
				description = "The bot does not have permission to perform the action requested, or Discord"\
								    " has forbidden it from performing this action for another reason. Ensure that"\
									" permissions for this server are configured correctly."

			case utils.BadMessageResponse:
				title = "Message response contains incorrect content"
				description = "The bot message you are responding to does not accept this content."\
									" Check that you have followed the instructions correctly and try again."
			
			case utils.CustomCommandError: 
				title = error.title
				description = error.desc
			
			case _:
				title = "Unknown error"
				description = "Heraldtron has encountered an unforseen difficulty. An error report has been sent."
				warn = True
				
		if warn:
			self.bot.logger.warning(
				f"{type(error).__name__}: {str(error)}\n {''.join(traceback.format_tb(error.__traceback__))}"
			)
		
		return views.Generic(
			title, description, heading = f"{views.ERROR_EMOJI} An error has been encountered"
		)
	
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		mention = None
	
		if not isinstance(ctx.channel, discord.abc.GuildChannel):
			ctx.bot.active_dms.discard(ctx.channel.id)
	
		if (
			(isinstance(error, commands.CommandNotFound) and re.match(BotErrors.IGNORE_PAT, ctx.message.content))
			or isinstance(error, utils.CommandCancelled)
		):
			return
		elif isinstance(error, commands.HybridCommandError):
			error = error.original

		elif isinstance(error, commands.CommandInvokeError):
			error = error.original
			mention = (await self.bot.application_info()).owner.mention
	
		await ctx.send(view = await self.respond_to_error(error, mention))

	async def on_app_command_error(self, interaction, error):
		view = await self.respond_to_error(error, None)
		
		if interaction.response.is_done():
			await interaction.followup.send(view = view)
			return
		
		await interaction.response.send_message(
			view = view,
			ephemeral = interaction.extras.get("ephemeral_error", False)
		)

async def setup(bot):
	await bot.add_cog(BotErrors(bot))
