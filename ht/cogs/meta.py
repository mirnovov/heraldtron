import discord, aiohttp, aiosqlite, platform, os, re
from discord import ui
from discord.ext import commands
from .. import utils, views, __copyright__, __version__

class MetaTools(utils.MeldedCog, name = "Meta", category = "Other", limit = False):
	RNAMES = re.compile("(?m)^(?:NAME|VERSION_ID)=\"?(.+?)\"?\n")

	def __init__(self, bot):
		self.bot = bot
		self.commit = self.get_commit_hash()

		bot.help_command = MeldedHelpCommand()
		bot.help_command.cog = self

	@commands.hybrid_command(
		help = "Checks the bot's ping to the Discord server.",
		aliases = ("pn",)
	)
	async def ping(self, ctx):
		await ctx.send(f":stopwatch: | Pong! The message latency was **{(self.bot.latency * 1000):4f} ms**.")

	@commands.hybrid_command(
		help = "Displays information about this bot.",
		aliases = ("ab",)
	)
	async def about(self, ctx):
		prefix_command_count = len([*filter(lambda c: not c.extras.get("resource"), self.bot.commands)])
		api_version = discord.http.INTERNAL_API_VERSION
		view = ui.LayoutView()
		
		top = ui.Section(
			ui.TextDisplay(f"## Heraldtron\n**{__version__} {self.commit}**\n\n{self.bot.description}"),
			accessory = ui.Thumbnail(media = str(self.bot.user.display_avatar.with_size(512).url))
		)

		info = ui.TextDisplay(
			f"\n### Running on\n"
			f"**Python {platform.python_version()}**\t"
			f"`{platform.python_implementation()} ({platform.python_build()[0]}"
			f" {platform.python_build()[1].replace('  ',' ')})`\n"
			f"**{self.get_os_name()}**\t`{self.get_os_details()}`"
			f"\n### Made with the help of\n"
			f"**[discord.py](https://pypi.org/project/discord.py/) {discord.__version__}**\n"
			f"**[aiohttp](https://pypi.org/project/aiohttp/) {aiohttp.__version__}**\n"
			f"**[aiosqlite](https://pypi.org/project/aiosqlite/) {aiosqlite.__version__}**"
			f" and the [SQLite](https://www.sqlite.org/) library"
			f"\n### And special thanks to\n"
			f"Ensix, GreiiEquites, and every "
			f"[contributor](https://github.com/mirnovov/heraldtron/graphs/contributors) to the project"
			f"\n\n-# API version {api_version} \u00B7 {len(self.bot.guilds)} servers \u00B7"
			f" {len(self.bot.users)} users \u00B7 ≤{self.bot._connection.max_messages} cached messages" 
			f" \u00B7 {prefix_command_count} prefix commands \u00B7 {len(self.bot.tree.get_commands())} app commands"
			f"\n-# {__copyright__}. This is an open source project available under the MIT license."
		)
		
		actionrow = ui.ActionRow(
			ui.Button(
				label = "Visit the Heraldry Discord",
				style = discord.ButtonStyle.secondary,
				url = "https://discord.gg/Wvsz2M36nt"
			), 
			ui.Button(
				label = "Edit on GitHub",
				style = discord.ButtonStyle.secondary,
				url = "https://github.com/mirnovov/heraldtron"
			)
		)
		
		view.add_item(ui.Container(top, info, actionrow))

		await ctx.send(view = view)

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
		
	@staticmethod
	def get_commit_hash():
		return os.popen("git rev-parse --short=7 HEAD").read().strip()

class MeldedHelpCommand(commands.DefaultHelpCommand):
	def __init__(self,**options):
		super().__init__(**options)
		self.command_attrs.update({
			"brief": "Look up the functionality of commands.",
		    "help": "Look up the functionality of commands.\n"
					"Follow with `command` for more info on a command,"
					" and `category` for more info on a category."
		})

	def sort_melded_cogs(self, key):
		if key == "Other": return "zzzz"
		elif key == "Heraldry": return "AAAA"
		return key

	async def send_bot_help(self, mapping):
		bot = self.context.bot
		pages = []

		for key in sorted(self.context.bot.melded_cogs, key = self.sort_melded_cogs):
			page = self.context.bot.melded_cogs[key]
			text, valid = await self.send_melded_cog_help(key, page)
			if valid: pages.append((key, text))

		view = views.HelpSwitcher(pages)
		message = await self.context.send(view = view)

		view.message = message

	async def send_melded_cog_help(self, title, cogs):
		text = ""
		valid = {}

		for cog in cogs:
			commands = await self.filter_commands(cog.get_commands(), sort = self.sort_commands)
			if not commands: continue

			value = f"{cog.description}\n" if cog.description else ""
			valid[cog.qualified_name] = f"{value}{self.add_indented_commands(commands, heading = None)}"

		if len(valid) == 1:
			text += f"### {title}\n" + next(iter(valid.values()))
		else:
			for name, desc in valid.items():
				text += f"### {name}\n{desc}"

		return text, valid

	async def send_cog_help(self, cog):
		text, _ = await self.send_melded_cog_help(cog.qualified_name, [cog])
		view = views.Generic("", 
			f"-# {views.HelpSwitcher.INFO}\n" +
			text, 
			heading = views.HelpSwitcher.HEADING
		)
		await self.get_destination().send(view = view)

	async def send_command_help(self, command):
		view = views.Generic(command.name, command.description or "", heading = views.HelpSwitcher.HEADING)
		view.add_text(self.add_command_formatting(command))
		await self.get_destination().send(view = view)

	async def send_group_help(self, group):
		view = views.Generic(
			group.name,
			group.description or "", 
			heading = views.HelpSwitcher.HEADING
		)
		view.add_text(self.add_command_formatting(group) + "\n")

		teeth = await self.filter_commands(group.commands, sort = self.sort_commands)
		view.add_text(self.add_indented_commands(teeth, heading = "Subcommands"))

		await self.get_destination().send(view = view)

	async def send_error_message(self, error):
		await self.get_destination().send(view = views.Generic(
			"Invalid help entry", error, heading = f"{views.ERROR_EMOJI} An error has been encountered"
		))

	def add_command_formatting(self, command):
		desc = "\n"
		if signature := self.get_command_signature(command):
			desc += signature
		if command.help:
			desc += "\n\n" + command.help.rstrip("\u0060")

		return desc

	def get_ending_note(self):
		return "Type !help [command] for more info on a command, including aliases."

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

		return f"`{self.context.clean_prefix}{primary_name} {self.list_params(command)}`{aliases}"

	@staticmethod
	def list_params(command):
		#an override of command.signature; placed here as it's not worth overriding
		#the whole class for this
		if command.usage is not None: return command.usage

		params = command.clean_params
		if not params: return ""

		result = []
		for name, param in params.items():
			greedy = isinstance(param.annotation, commands.converter.Greedy)

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
		desc = f"**{heading}**\n" if heading else ""

		if not commands: desc += f"No commands available right now."
		for command in commands:
			desc += f"- **{command.name}**:   {command.short_doc}\n"

		return desc

async def setup(bot):
	await bot.add_cog(MetaTools(bot))
