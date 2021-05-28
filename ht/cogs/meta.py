import discord, aiohttp, aiosqlite, platform, os, re
from discord.ext import commands
from .. import utils, embeds, __version__

class MetaTools(commands.Cog, name = "Meta"):
	RNAMES = re.compile("(?m)^(?:NAME|VERSION_ID)=(.+)")
	
	def __init__(self, bot):
		self.bot = bot
		bot.help_command = NvHelpCommand()
		bot.help_command.cog = self
		
	@commands.command(
		help = "Checks the bot's ping to the Discord server.",
		aliases = ("pn",)
	)
	async def ping(self, ctx):
		await ctx.send(f":stopwatch: | Pong! The message latency was **{(self.bot.latency * 1000):4f} ms**.")
		
	@commands.command(
		help = "Displays information about this bot.",
		aliases = ("ab",)
	)
	async def about(self, ctx):
		embed = embeds.ABOUT.create(f"Heraldtron {__version__}", self.bot.description)
		embed.url = "https://github.com/mirnovov/heraldtron"
		embed.set_thumbnail(url = str(self.bot.user.avatar_url_as(size = 512)))
		
		embed.add_field(
			name="Developed using", 
			value=f"**Python {platform.python_version()}**\n"\
				  f"`{platform.python_implementation()} ({platform.python_build()[0]}"\
				  f" {platform.python_build()[1].replace('  ',' ')})`",  
			inline=True
		)
		embed.add_field(
			name = "Running on", 
			value = f"**{self.get_os_name()}**\n`{self.get_os_details()}`", 
			inline = True
		)
		
		embed.add_field(
			name = "Made with the help of", 
			value = f"- [discord.py](https://pypi.org/project/discord.py/) `{discord.__version__}`\n"\
				    f"- [aiohttp](https://pypi.org/project/aiohttp/) `{aiohttp.__version__}`\n"
					f"- [aiosqlite](https://pypi.org/project/aiosqlite/) `{aiosqlite.__version__}`"\
					" and the [SQLite](https://www.sqlite.org/) library", 
			inline = False
		)
		embed.add_field(
			name = "And special thanks to", 
			value = "- Will\n- Ensix\n- GreiiEquites",
			inline = False
		)
		embed.set_footer(text="© novov 2021. This is an open source project available under the MIT license.")
		
		await ctx.send(embed=embed)	
		
	def get_os_name(self):
		if os.path.exists("/etc/os-release"):
			with open("/etc/os-release") as file:
				os_release = file.read()
			rname = re.findall(self.RNAMES, os_release)
			return f"{rname[0]} {rname[1]}"
		
		return platform.platform(terse = True).replace("-", " ")	
		
	def get_os_details(self):
		uname = platform.uname()
		dedup = uname.release.removesuffix(f".{uname.machine}")
		return f"{uname.system} {dedup} ({uname.machine})"

class NvHelpCommand(commands.DefaultHelpCommand):
	def __init__(self,**options):
		super().__init__(**options)
		self.command_attrs.update({
			"brief": "Look up the functionality of commands.",
		    "help": "Look up the functionality of commands.\n"
					"Follow with `command` for more info on a command,"
					" and `category` for more info on a category."
		})
	
	async def send_bot_help(self, mapping):
		bot = self.context.bot
		pages = []
		cogs = sorted(
			self.context.bot.cogs,
			key = lambda c: "z" if c == "Meta" else c
		)
		
		for cog in cogs:
			embed, teeth = await self.send_cog_help(bot.get_cog(cog), send = False)
			if teeth: pages.append(embed)
			
		for i, embed in enumerate(pages, start = 1):
			embed.set_author(icon_url = embeds.HELP.icon_url, name = f"Command help ({i}/{len(pages)})")
			
		await embeds.paginate(self.context, lambda i: pages[i], len(pages))
		
	async def send_cog_help(self, cog, send = True):
		embed = embeds.HELP.create(
			f"{cog.qualified_name} commands", 
			f"{cog.description}\n" if cog.description else "",
		)
		
		teeth = await self.filter_commands(cog.get_commands(), sort = self.sort_commands)
		embed.description += self.add_indented_commands(teeth, heading = None)

		if note := self.get_ending_note():
			embed.set_footer(text = note)
			
		if send: await self.get_destination().send(embed = embed)
		else: return embed, teeth
		
	async def send_command_help(self, command):
		embed = embeds.HELP.create(command.name, command.description or "")
		embed.description += self.add_command_formatting(command)
		await self.get_destination().send(embed = embed)
		
	async def send_group_help(self, group):
		embed = embeds.HELP.create(group.name, group.description or "")
		embed.description += self.add_command_formatting(group) + "\n"

		teeth = await self.filter_commands(group.commands, sort = self.sort_commands)
		embed.description += self.add_indented_commands(teeth, heading = "Subcommands")

		if note := self.get_ending_note():
			embed.set_footer(text = note)

		await self.get_destination().send(embed = embed)
		
	async def send_error_message(self, error):
		await self.get_destination().send(embed = embeds.ERROR.create(
			"Invalid help entry", error
		))
		
	def add_command_formatting(self, command):
		desc = "\n"
		if signature := self.get_command_signature(command):
			desc += signature 
		if command.help:
			desc += "\n\n" + command.help.rstrip("\u0060")
			
		return desc
			
	def get_ending_note(self):
		return "Type !help [command] for more info on a command."
		
	def get_command_signature(self, command):
		parent = command.parent
		entries = []
		
		while parent is not None:
			if not parent.signature or parent.invoke_without_command:
				entries.append(parent.name)
			else:
				entries.append(f"{parent.name} {self.list_params(parent)}")
			parent = parent.parent
		parent_sig = " ".join(reversed(entries))

		primary_name = command.name if not parent_sig else f"{parent_sig} {command.name}"
		aliases = ""
		
		if len(command.aliases) > 0:
			alias_list = ", ".join(f"`{a}`" for a in command.aliases)
			aliases = f"\n**Aliases**: {alias_list}"

		return f"`{self.clean_prefix}{primary_name} {self.list_params(command)}`{aliases}"
	
	@staticmethod	
	def list_params(command):
		#an override of command.signature; placed here as it's not worth overriding
		#the whole class for this
		if command.usage is not None: return command.usage

		params = command.clean_params
		if not params: return ""

		result = []
		for name, param in params.items():
			greedy = isinstance(param.annotation, commands.converter._Greedy)

			if param.default is not param.empty:
				if (isinstance(param.default, str) and param.default) or param.default is not None:
					result.append(f"({name})" if not greedy else f"({name})...")
				else:
					result.append(f"({name})")

			elif param.kind == param.VAR_POSITIONAL or greedy:
				result.append(f"{name}...")
			else:
				result.append(name)

		return " ".join(result)
	
	def add_indented_commands(self, commands, *, heading):
		desc = f"\u200b\n**{heading}**\n" if heading else ""
		
		if not commands: desc += f"No commands available right now." 
		for command in commands:
			desc += f"- **{command.name}**:   {command.short_doc}\n"
			
		return desc
	
def setup(bot):
	bot.add_cog(MetaTools(bot))