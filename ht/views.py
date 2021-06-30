import discord, asyncio, random
from discord import ui
from . import utils

LONG_TIMEOUT = 1000

def disable_dm_commands(func): 
	#Unprefixed commands must be disabled for certain responses
	
	async def wrapper(*args, **kwargs):
		ctx = args[0]
		
		if not isinstance(ctx.channel, discord.abc.GuildChannel):
			ctx.bot.active_dms.add(ctx.channel.id)
			result = await func(*args, **kwargs)
			ctx.bot.active_dms.discard(ctx.channel.id)
		else:
			result = await func(*args, **kwargs)  
		return result
		
	return wrapper

class Navigator(ui.View):
	def __init__(self, embeds):
		super().__init__()
		
		for i, embed in enumerate(embeds, start = 1):
			embed.set_author(
				name = f"{embed.author.name} ({i}/{len(embeds)})", 
				icon_url = embed.author.icon_url
			)
		
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
		
	async def on_timeout(self):
		self.clear_items()
		
class HelpSwitcher(ui.View):
	def __init__(self, embeds):
		super().__init__()
		tuple(self.add_help(name, embed) for name, embed in embeds.items())
			
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
		self.clear_items()
		
class Confirm(ui.View):
	def __init__(self, action, author = None):
		super().__init__()
		
		self.result = None
		self.author = author
		
		confirm = ui.Button(label = action, style = discord.ButtonStyle.success)
		confirm.callback = lambda i: self.interact(True, i)
		self.add_item(confirm)
		
		cancel = ui.Button(label = "Cancel", style = discord.ButtonStyle.danger)
		cancel.callback = lambda i: self.interact(False, i)
		self.add_item(cancel)
		
	async def interaction_check(self, interaction):
		return True if not self.author else interaction.user == self.author
		
	@staticmethod
	async def run(ctx, info, action = "Continue"):
		view = Confirm(action, author = ctx.author)
		message = await ctx.send(info, view = view)
		
		await view.wait()
		await message.edit(view = None)
		
		if view.result == None:
			raise await utils.CommandCancelled.create("Command timed out", ctx)
		elif not view.result:
			raise await utils.CommandCancelled.create("Command cancelled", ctx)
		else:
			await message.edit(content = ":white_check_mark: | Confirmed.")
	
	async def interact(self, result, interaction):
		await interaction.response.pong()
		self.result = result
		self.stop()
		
class Chooser(ui.View):
	def __init__(self, ctx, choices):
		super().__init__(**kwargs)
		
		self.pressed = None
		self.ctx = ctx

		for i, choice in enumerate(choices):
			self.add_button(ui.Button(label = choice, style = discord.ButtonStyle.primary), i)
		
		self.add_button(ui.Button(label = "Cancel", style = discord.ButtonStyle.danger), "Cancel")
			
	async def interaction_check(self, interaction):
		return True if not self.ctx.author else interaction.user == self.ctx.author
			
	@staticmethod
	@disable_dm_commands
	async def run(ctx, info, choices, **kwargs):
		view = Chooser(ctx, choices, **kwargs)
		
		message = await ctx.send(info, view = view)
		await view.wait()
		await message.edit(view = None)
		
		return await view.get_result()
			
	async def get_result(self):
		if self.pressed == "Cancel":
			raise await utils.CommandCancelled.create("Command cancelled", self.ctx)
		
		return self.pressed
			
	def add_button(self, button, indice):
		async def primitive(interaction):
			await interaction.response.pong()
			self.pressed = indice
			self.stop()
		
		button.callback = primitive
		self.add_item(button)
		
class RespondOrReact(Chooser):
	def __init__(self, ctx, **kwargs):
		super().__init__(ctx, tuple(), **kwargs)
	
	@staticmethod
	@disable_dm_commands
	async def run(ctx, info, additional = tuple(), added_check = None, **kwargs):
		def check_message(message):
			if ctx.author != message.author: return False
			elif added_check: return added_check(message)
			return True
			
		view = RespondOrReact(ctx, **kwargs)
		tuple(view.add_button(item, item.label) for item in additional)			
		
		message = await ctx.send(info, view = view)
		done, pending = await asyncio.wait(
			(view.wait(), ctx.bot.wait_for("message", check = check_message, timeout = view.timeout)), 
			return_when = asyncio.FIRST_COMPLETED
		)
		
		for future in pending: future.cancel()	#ignore anything else
		for future in done: future.exception() #retrieve and ignore any other completed future's exception
		
		await message.edit(view = None)
		
		try:
			return await view.get_result() or done.pop().result()
		except asyncio.TimeoutError:
			raise await utils.CommandCancelled.create("Command timed out", self.ctx)
			
class TriviaButton(ui.Button):
	def __init__(self, label, users):
		super().__init__(label = label, style = discord.ButtonStyle.primary)
		self.users = users
	
	async def callback(self, interaction):
		mention = interaction.user.mention
		
		if mention not in self.users:
			self.users[mention]	= self.label		
			await interaction.response.pong()
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