import discord, asyncio, random
from discord import ui
from discord.ext import commands
from . import utils

ERROR_EMOJI = "<:error:1407259518470983710>"

class NvViewBase():
	async def terminate(self, interaction):
		for child in self.walk_children():
			child.disabled = True
		
		try:
			if interaction:
				await interaction.response.edit_message(view = self)
			elif getattr(self, "message", None):		
				await self.message.edit(view = self)
		
		except discord.NotFound:
			pass
				
		self.stop()

class NvView(NvViewBase, ui.View):
	async def on_timeout(self):
		await self.terminate(None)
		
class NvLayoutView(NvViewBase, ui.LayoutView):
	async def on_timeout(self):
		await self.terminate(None)

def disable_dm_commands(func):
	#Unprefixed commands must be disabled for certain responses
	async def wrapper(*args, **kwargs):
		ctx = args[0] if type(args[0]) == commands.Context else args[0].ctx

		if not isinstance(ctx.channel, discord.abc.GuildChannel):
			ctx.bot.active_dms.add(ctx.channel.id)
			result = await func(*args, **kwargs)
			ctx.bot.active_dms.discard(ctx.channel.id)
		else:
			result = await func(*args, **kwargs)
		return result

	return wrapper
	
class Navigator(NvView):
	def __init__(self, ctx, embeds):
		super().__init__()

		for i, embed in enumerate(embeds, start = 1):
			embed.set_author(
				name = f"{embed.author.name} ({i}/{len(embeds)})",
				icon_url = embed.author.icon_url
			)

		self.ctx = ctx
		self.index = 0
		self.embeds = embeds

		self.add_nav("<:first:859371978612015136>", lambda: 0, disabled = True)
		self.add_nav("<:prev:859371979035377694>", lambda: self.index - 1, disabled = True)
		self.add_nav("<:random:859371979093442580>", lambda: random.randrange(0, len(self.embeds)), False)
		self.add_nav("<:next:859371979026071582>", lambda: self.index + 1)
		self.add_nav("<:last:859371979026464778>", lambda: len(self.embeds) - 1)

	def add_nav(self, emoji, index, primary = True, **kwargs):
		async def switch(interaction):
			self.index = index()

			for child in self.children[:2]:
				child.disabled = self.index == 0

			for child in self.children[-2:]:
				child.disabled = self.index == len(self.embeds) - 1

			await interaction.response.edit_message(embed = self.embeds[self.index], view = self)

		style = discord.ButtonStyle.primary if primary else discord.ButtonStyle.secondary
		button = ui.Button(emoji = emoji, style = style, **kwargs)
		button.callback = switch

		self.add_item(button)

	async def run(self):
		self.message = await self.ctx.send(embed = self.embeds[0], view = self)

class HelpSwitcher(NvLayoutView):
	HEADING = ":information_source: Command help"
	FOOTER = "Type !help [command] for more info on a command, including aliases."
	
	def __init__(self, pages):
		super().__init__()
		
		self.container = ui.Container()
		self.actionrow = ui.ActionRow()
		self.text = ui.TextDisplay(pages[0][1] + "\u200b")

		[self.add_help(name, v) for name, v in pages]

		self.actionrow.children[0].disabled = True
		
		self.container.add_item(ui.TextDisplay(f"-# **{self.HEADING}**"))
		self.container.add_item(self.text)
		self.container.add_item(self.actionrow)
		self.container.add_item(ui.TextDisplay(f"-# {self.FOOTER}"))

		self.add_item(self.container)

	def add_help(self, name, page):
		async def switch(interaction):
			for child in self.actionrow.children:
				child.disabled = child.label == name
			
			self.text.content = page + "\u200b"
			await interaction.response.edit_message(view = self)

		button = ui.Button(label = name, style = discord.ButtonStyle.primary)
		button.callback = switch

		self.actionrow.add_item(button)

class Chooser(NvView):
	def __init__(self, ctx, choices, placeholder, **kwargs):
		super().__init__(**kwargs)
		self.ctx = ctx
		self.success = False
		self.select = ui.Select(placeholder = placeholder)
		
		for i, choice in enumerate(choices):
			choice.value = str(i)
			self.select.append_option(choice)
		
		self.select.callback = self.select_callback
		self.add_item(self.select)
		
		cancel = ui.Button(label = "Cancel", style = discord.ButtonStyle.red)
		cancel.callback = self.cancel
		cancel.row = 2
		self.add_item(cancel)
	
	async def select_callback(self, interaction):
		await self.terminate(interaction)
	
	@disable_dm_commands
	async def run(self, info):
		self.message = await self.ctx.send(info, view = self)
		await self.wait()
		
		if self.select.values:
			return int(self.select.values[0])
		
		raise utils.CommandCancelled()
			
	async def cancel(self, interaction):
		await self.terminate(interaction)
	
	async def interaction_check(self, interaction):
		return True if not self.ctx.author else interaction.user == self.ctx.author
	
	async def on_timeout(self):
		self.chosen = -1
		await self.terminate(None)

class TriviaButton(ui.Button):
	def __init__(self, label, users):
		super().__init__(label = label, style = discord.ButtonStyle.primary)
		self.users = users

	async def callback(self, interaction):
		mention = interaction.user.mention

		if mention not in self.users:
			self.users[mention]	= self.label
			await interaction.response.defer()
		else:
			subview = ui.View()
			undo_button = ui.Button(label = "Undo", style = discord.ButtonStyle.danger)
			undo_button.callback = self.undo
			subview.add_item(undo_button)

			await interaction.response.send_message(
				content = ":x: | You've already responded.", ephemeral = True, view = subview
			)

	async def undo(self, interaction):
		del self.users[interaction.user.mention]
		await interaction.response.pong()

		await interaction.response.edit_message(
			content = ":leftwards_arrow_with_hook: | Your response has been undone.", view = None
		)
		
class Generic(ui.LayoutView):
	def __init__(self, title, description, heading = None, thumbnail = None):
		super().__init__()
		
		self.container = ui.Container()
		text = ""
		
		if heading:
			self.container.add_item(ui.TextDisplay(f"-# **{heading}**\n"))
			
		if title:
			text += f"## {title}"
			
		if description:
			if title: text += "\n"
			text += description
			
		if text:
			self.text = ui.TextDisplay(text)
		
			if thumbnail:
				self.container.add_item(ui.Section(
					self.text,
					accessory = ui.Thumbnail(thumbnail)
				))
			else:
				self.container.add_item(self.text)
		
		self.add_item(self.container)
		
	def add_image(self, url):
		gallery = ui.MediaGallery()
		gallery.add_item(media = url)
		self.container.add_item(gallery)
		
	def add_text(self, text):
		self.text.content += text
	
	def add_footer(self, text):
		self.container.add_item(ui.TextDisplay(f"-# {text}"))
