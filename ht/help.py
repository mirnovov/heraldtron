import discord, itertools
from discord.ext import commands

class NvHelpCommand(commands.DefaultHelpCommand):
	def __init__(self,**options):
		super().__init__(**options)
		
		self.no_category = "Help"
		self.embed = discord.Embed(color=0x3365ca, description="")
		self.embed.set_author(
			name="Command help",
			icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/OOjs_UI_icon_info-progressive.svg/"\
			"240px-OOjs_UI_icon_info-progressive.svg.png"
		)
	
	async def send_pages(self):
		destination = self.get_destination()
		await destination.send(embed=self.embed)
	
	async def send_bot_help(self, mapping):
		ctx = self.context
		bot = ctx.bot

		self.embed.description += "You can execute a variety of useful actions using Heraldtron.\n\u200b"

		def get_category(command, *, no_category=f"\u200b{self.no_category}:"):
			cog = command.cog
			return cog.qualified_name + ":" if cog is not None else no_category

		filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
		max_size = self.get_max_size(filtered)
		to_iterate = itertools.groupby(filtered, key=get_category)

		for category, commands in to_iterate:
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
			self.embed.description += "\n" + command.help.rstrip("\u0060")
		
	async def send_group_help(self, group):
		self.add_command_formatting(group)

		filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
		self.add_indented_commands(filtered, heading=self.commands_heading)

		if filtered:
			note = self.get_ending_note() or ""
			if note:
				self.embed.set_footer(text="".join(note))

		await self.send_pages()
	
	def add_indented_commands(self, commands, *, heading, max_size=None):
		if not commands: return

		self.embed.description+= f"\u200b\n**{heading}**\n"
		for command in commands:
			self.embed.description+= f"- **{command.name}**:   {command.short_doc}\n"
			
		self.embed.description += ""