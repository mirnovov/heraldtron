import discord, aiohttp, traceback, logging, json, re
from discord.ext import commands
from .. import utils, embeds

class BotErrors(commands.Cog, name = "Bot Errors"):
	ERROR_MESSAGES = {
		commands.CommandNotFound: (
			"Command not found",
			"The command you entered does not exist. Check your spelling and try again.",
			False
		),
		commands.NoPrivateMessage: (
			"Command must be public",
			"The command you entered cannot be used during direct messaging.",
			False
		),
		commands.MissingRole: (
			"Command requires elevated privileges",
			"The command you entered requires a role that you do not possess.",
			False
		),
		commands.MissingRequiredArgument: (
			"Command is missing argument",
			"The command you entered requires you to enter `{error.param.name}`. Check that it is entered correctly and try again.",
			False
		),
		commands.UserNotFound: (
			"Command could not locate user",
			"The command you entered requires a valid user. Check that their name is mentioned correctly and try again.",
			False
		),
		commands.TooManyArguments: (
			"Command given too many arguments",
			"The command you entered does not accept this many arguments. Check that you are using it correctly and try again.",
			False
		),
		commands.NotOwner: (
			"Command requires elevated privileges",
			"The command you entered is solely permitted to be used by the bot owner.",
			False
		),
		commands.BadArgument: (
			"Command given invalid argument",
			"One or more of the arguments you entered is invalid. Check that the command is correct and try again.",
			False
		),
		aiohttp.ClientConnectionError: (
			"Could not connect to server",
			"The server that the bot is trying to reach cannot connect. An error report has been sent."
			" If the problem persists, contact {mention}.",
			True
		),
		json.JSONDecodeError: (
			"Could not decode server response",
			"The server has returned undecodable content. An error report has been sent."
			" If the problem persists, contact {mention}.",
			True
		),
		aiohttp.ContentTypeError: (
			"Could not decode server response",
			"The server has returned content of the incorrect type. An error report has been sent."
			" If the problem persists, contact {mention}.",
			True
		),
		utils.BadMessageResponse: (
			"Message response contains incorrect content",
			"The bot message you are responding to does not accept this content."
			" Check that you have followed the instructions correctly and try again.",
			False
		),
		utils.CustomCommandError: ("{error.title}", "{error.desc}", False)
	}

	IGNORE_PAT = re.compile(r"!(!|\?)") #ignore "!!!" etc

	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		mention, warn = None, False

		if not isinstance(ctx.channel, discord.abc.GuildChannel):
			ctx.bot.active_dms.discard(ctx.channel.id)

		if (
			(isinstance(error, commands.CommandNotFound) and re.match(BotErrors.IGNORE_PAT, ctx.message.content))
			or isinstance(error, utils.CommandCancelled)
		):
			return
		elif isinstance(error, commands.CommandInvokeError):
			error = error.original
			mention = (await self.bot.application_info()).owner.mention

		if isinstance(error, tuple(BotErrors.ERROR_MESSAGES)):
			message = tuple(y for x, y in BotErrors.ERROR_MESSAGES.items() if isinstance(error, x))[0]
			embed = embeds.ERROR.create(
				message[0].format(error = error),
				message[1].format(error = error, mention = mention)
			)

			await ctx.send(embed = embed)
			warn = message[2]
		else:
			await ctx.send(embed = embeds.ERROR.create(
				"Unknown error",
				"Heraldtron has encountered an unforseen difficulty. An error report has been sent."
			))
			warn = True

		if warn:
			self.bot.logger.warning(
				f"{type(error).__name__}: {str(error)}\n {''.join(traceback.format_tb(error.__traceback__))}"
			)

def setup(bot):
	bot.add_cog(BotErrors(bot))
