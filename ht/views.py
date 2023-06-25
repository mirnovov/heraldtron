import discord, asyncio, random
from discord import ui
from discord.ext import commands
from . import utils

LONG_TIMEOUT = 1000

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

class Navigator(ui.View):
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

	async def on_timeout(self):
		await self.message.edit(embed = self.embeds[self.index], view = None)

class HelpSwitcher(ui.View):
	def __init__(self, embeds):
		super().__init__()
		[self.add_help(name, embed) for name, embed in embeds]

		self.children[0].disabled = True

	def add_help(self, name, embed):
		async def switch(interaction):
			for child in self.children:
				child.disabled = child.label == name

			await interaction.response.edit_message(embed = embed, view = self)

		button = ui.Button(label = name, style = discord.ButtonStyle.primary)
		button.callback = switch

		self.add_item(button)

	async def on_timeout(self):
		if not hasattr(self, "message"): return
		await self.message.edit(embed = self.message.embeds[0], view = None)

class UserSelector(ui.View):
	def __init__(self, ctx, **kwargs):
		super().__init__(**kwargs)
		self.ctx = ctx
		self.chosen = None

		self.add_button(ui.Button(label = "Cancel", style = discord.ButtonStyle.red), -1)

	async def interaction_check(self, interaction):
		return True if not self.ctx.author else interaction.user == self.ctx.author

	def add_button(self, button, indice):
		async def primitive(interaction):
			self.chosen = indice
			self.stop()

		button.callback = primitive
		button.row = 2
		self.add_item(button)

	async def get_choice(self):
		if self.chosen == -1:
			raise await utils.CommandCancelled.create("Command cancelled", self.ctx)
		try:
			return self.chosen
		except asyncio.TimeoutError:
			raise await utils.CommandCancelled.create("Command timed out", self.ctx)

	@disable_dm_commands
	async def run(self, info):
		self.message = await self.ctx.send(info, view = self)
		await self.wait()
		await self.message.edit(view = None)
		return await self.get_choice()

class Chooser(UserSelector):
	def __init__(self, ctx, choices, action, style = discord.ButtonStyle.success, **kwargs):
		super().__init__(ctx, **kwargs)
		self.chosen = 0

		self.select = ui.Select()
		self.add_item(self.select)

		for i, choice in enumerate(choices):
			choice.value = str(i)
			choice.default = i == 0
			self.select.append_option(choice)

		confirm = ui.Button(label = action, style = style)
		confirm.callback = self.choose
		confirm.row = 2
		self.add_item(confirm)

	async def choose(self, interaction):
		if self.select.values:
			self.chosen = int(self.select.values[0])

		self.stop()

class RespondOrReact(UserSelector):
	def __init__(self, ctx, additional = tuple(), added_check = None, **kwargs):
		super().__init__(ctx, **kwargs)

		self.added_check = added_check
		tuple(self.add_button(item, item.label) for item in additional)

	@disable_dm_commands
	async def run(self, info):
		def check_message(message):
			if self.ctx.author != message.author: return False
			elif self.added_check: return self.added_check(message)
			return True

		message = await self.ctx.send(info, view = self)
		
		t_wait = asyncio.create_task(self.wait())
		t_message = asyncio.create_task(
			self.ctx.bot.wait_for("message", check = check_message, timeout = self.timeout)
		)
		done, pending = await asyncio.wait((t_wait, t_message), return_when = asyncio.FIRST_COMPLETED)

		for future in pending: future.cancel()	#ignore anything else
		for future in done: future.exception() #retrieve and ignore any other completed future's exception

		await message.edit(view = None)
		return await self.get_choice() or done.pop().result()

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
