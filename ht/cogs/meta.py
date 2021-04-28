import discord, aiohttp, aiosqlite, itertools, sys, platform
from discord.ext import commands
from .. import utils, version

class MetaTools(commands.Cog, name="Meta"):
	def __init__(self, bot):
		self.bot = bot
		bot.help_command = NvHelpCommand()
		bot.help_command.cog = self
		
	@commands.command(
		help="Checks the bot's ping to the Discord server.",
		aliases=("pn",)
	)
	async def ping(self, ctx):
		await ctx.send(f":stopwatch: | Pong! The message round-trip took **{(self.bot.latency * 1000):4f} ms**.")
		
	@commands.command(
		help="Displays information about this bot.",
		aliases=("ab",)
	)
	async def about(self, ctx):
		embed = utils.nv_embed(
			f"Heraldtron {version.__version__}",
			self.bot.description,
			kind=5
		)
		embed.url = "https://github.com/mirnovov/heraldtron"
		embed.set_thumbnail(url=str(self.bot.user.avatar_url_as(size=512)))
		
		embed.add_field(
			name="Developed using", 
			value=f"**Python {platform.python_version()}**\n"\
				  f"`{platform.python_implementation()} ({platform.python_build()[0]}"\
				  f" {platform.python_build()[1]})`",  
			inline=True
		)
		embed.add_field(
			name = "Running on", 
			value = f"**{platform.uname().system} {platform.uname().release}**\n"\
				  f"`{platform.platform()}`", 
			inline = True
		)
		embed.add_field(
			name = "Made with the help of", 
			value = f" - [discord.py](https://pypi.org/project/discord.py/) `{discord.__version__}`\n"\
				    f" - [aiohttp](https://pypi.org/project/aiohttp/) `{aiohttp.__version__}`\n"
					f" - [aiosqlite](https://pypi.org/project/aiosqlite/) `{aiosqlite.__version__}`"\
					" and the [SQLite](https://www.sqlite.org/) library", 
			inline = False
		)
		embed.add_field(
			name="And special thanks to", 
			value=" - Will\n - Ensix\n - GreiiEquites",
			inline=False
		)
		embed.set_footer(text="© novov 2021. This is an open source project available under the MIT license.")
		
		await ctx.send(embed=embed)		

class NvHelpCommand(commands.DefaultHelpCommand):
	def __init__(self,**options):
		super().__init__(**options)
		
		self.no_category = "Help"
		self.embed = utils.nv_embed("","\u200b",kind=2)
		self.command_attrs.update({
			"brief": "Look up the functionality of commands.",
		    "help": "Look up the functionality of commands.\n"\
					"Follow with `command` for more info on a command,"\
					" and `category` for more info on a category."
		})
	
	async def send_pages(self):
		destination = self.get_destination()
		await destination.send(embed=self.embed)
	
	async def send_bot_help(self, mapping):
		ctx = self.context
		bot = ctx.bot

		self.embed.description += "You can execute a variety of useful actions using Heraldtron.\n\u200b"

		def get_category(command):
			cog = command.cog
			return cog.qualified_name + ":" if cog is not None else f"\u200b{self.no_category}:"
			
		def cat_sorter(command):
			if command.cog.qualified_name == "Meta": return "zzzz"
			else: return get_category(command)

		filtered = await self.filter_commands(bot.commands, sort=True, key=cat_sorter)
		max_size = self.get_max_size(filtered)
		to_iterate = itertools.groupby(filtered, key=get_category)

		for category, commands in to_iterate:
			if category == "Debug:": continue #never show debug on the main list
			commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
			self.add_indented_commands(commands, heading=category, max_size=max_size)

		note = self.get_ending_note() or ""
		if note:
			self.embed.description += "\u200b"
			self.embed.set_footer(text="".join(note))

		await self.send_pages()
		
	def add_command_formatting(self, command):
		self.embed.title = command.name
		
		if command.description:
			self.embed.description += command.description

		signature = self.get_command_signature(command)
		
		if signature:
			self.embed.description += f"\u0060{signature}\u0060"
		if command.help:
			self.embed.description += "\n\n" + command.help.rstrip("\u0060")
		
	async def send_cog_help(self, cog):
		if cog.description:
			self.embed.description += cog.description
			
		self.embed.title = f"{cog.qualified_name} commands"

		filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
		self.add_indented_commands(filtered, heading=None)

		note = self.get_ending_note() or ""
		if note:
			self.embed.description += "\u200b"
			self.embed.set_footer(text="".join(note))

		await self.send_pages()
	
	def add_indented_commands(self, commands, *, heading, max_size=None):
		if heading:
			self.embed.description+= f"\u200b\n**{heading}**\n"
		
		if not commands:	
			self.embed.description += f"No commands available right now." 
			
		for command in commands:
			self.embed.description+= f"- **{command.name}**:   {command.short_doc}\n"
			
		self.embed.description += ""
		
	async def send_error_message(self, error):
		await self.get_destination().send(embed=utils.nv_embed(
			"Invalid help entry",
			error
		))
		
	#async def filter_commands(self, commands, *, sort=False, key=None):
	#TODO: hide mod commands
	
def setup(bot):
	bot.add_cog(MetaTools(bot))