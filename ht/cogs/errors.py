import discord, aiohttp, traceback, logging, json, re, sys
from discord.ext import commands
from .. import utils, embeds

class BotErrors(commands.Cog, name = "Bot Errors"):
	IGNORE_PAT = re.compile(r"!(!|\?)") #ignore "!!!" etc

	def __init__(self, bot):
		self.bot = bot
		self.bot.tree.on_error = self.on_app_command_error
	
	async def respond_to_error(self, error, mention):
		embed = embeds.ERROR.create("","")
		warn = False
		
		match type(error):
			case commands.DisabledCommand | commands.CommandNotFound:
				embed.title = "Command not found"
				embed.description = "The command you entered does not exist. Check your spelling and try again."
				
			case commands.NoPrivateMessage:
				embed.title = "Command must be public"
				embed.description = "The command you entered cannot be used during direct messaging."
				
			case commands.MissingRole:
				embed.title = "Command requires elevated privileges"
				embed.description = "The command you entered requires a role that you do not possess."
				
			case commands.MissingRequiredArgument:
				embed.title = "Command is missing argument"
				embed.description = f"The command you entered requires you to enter `{error.param.name}`. Check that it is entered correctly and try again."
				
			case commands.UserNotFound:
				embed.title = "Command could not locate user"
				embed.description = "The command you entered requires a valid user. Check that their name is mentioned correctly and try again."
				
			case commands.TooManyArguments:
				embed.title = "Command given too many arguments"
				embed.description = "The command you entered does not accept this many arguments. Check that you are using it correctly and try again."
				
			case commands.NotOwner:
				embed.title = "Command requires elevated privileges"
				embed.description = "The command you entered is solely permitted to be used by the bot owner."
				
			case commands.BadArgument:
				embed.title = "Command given invalid argument"
				embed.description = "One or more of the arguments you entered is invalid. Check that the command is correct and try again."
				
			case aiohttp.ClientConnectionError:
				warn = True
				embed.title = "Could not connect to server"
				embed.description = "The server that the bot is trying to reach cannot connect. An error report has been sent."\
									f" If the problem persists, contact {mention}."
				
			case json.JSONDecodeError:
				warn = True
				embed.title = "Could not decode server response"
				embed.description = "The server has returned undecodable content. An error report has been sent."\
								  	f" If the problem persists, contact {mention}."
				
			case aiohttp.ContentTypeError:
				warn = True
				embed.title = "Could not decode server response"
				embed.description = "The server has returned content of the incorrect type. An error report has been sent."\
								  	f" If the problem persists, contact {mention}."
			case utils.BadMessageResponse:
				embed.title = "Message response contains incorrect content"
				embed.description = "The bot message you are responding to does not accept this content."\
									" Check that you have followed the instructions correctly and try again."
			
			case utils.CustomCommandError: 
				embed.title = error.title
				embed.description = error.desc
			
			case _:
				embed.title = "Unknown error"
				embed.description = "Heraldtron has encountered an unforseen difficulty. An error report has been sent."
				warn = True
				
		if warn:
			self.bot.logger.warning(
				f"{type(error).__name__}: {str(error)}\n {''.join(traceback.format_tb(error.__traceback__))}"
			)
			
		return embed
	
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
	
		await ctx.send(embed = await self.respond_to_error(error, mention))

	async def on_app_command_error(self, interaction, error):
		await interaction.response.send_message(
			embed = await self.respond_to_error(error, None),
			ephemeral = interaction.extras.get("ephemeral_error", False)
		)

async def setup(bot):
	await bot.add_cog(BotErrors(bot))
