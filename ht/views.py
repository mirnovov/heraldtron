import discord, random
from discord import ui

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
		self.size = len(self.embeds) - 1
	
	@ui.button(emoji = "<:first:859371978612015136>", style = discord.ButtonStyle.primary, disabled = True)
	async def first_button(self, button, interaction):
		await self.modify(0, interaction)
	
	@ui.button(emoji = "<:prev:859371979035377694>", style = discord.ButtonStyle.primary, disabled = True)
	async def prev_button(self, button, interaction):
		await self.modify(self.index - 1, interaction)
		
	@ui.button(emoji = "<:random:859371979093442580>")
	async def random_button(self, button, interaction):
		await self.modify(random.randrange(0, self.size + 1), interaction)
	
	@ui.button(emoji = "<:next:859371979026071582>", style = discord.ButtonStyle.primary)
	async def next_button(self, button, interaction):
		await self.modify(self.index + 1, interaction)
		
	@ui.button(emoji = "<:last:859371979026464778>", style = discord.ButtonStyle.primary)
	async def last_button(self, button, interaction):
		await self.modify(self.size, interaction)
		
	async def modify(self, index, interaction):
		self.index = index
		
		if index == 0:
			self.prev_button.disabled = True
			self.first_button.disabled = True
		else: 
			self.prev_button.disabled = False
			self.first_button.disabled = False
			
		if index == self.size:
			self.next_button.disabled = True
			self.last_button.disabled = True
		else: 
			self.next_button.disabled = False
			self.last_button.disabled = False
		
		await interaction.response.edit_message(embed = self.embeds[self.index], view = self)
		
	async def on_timeout(self):
		self.clear_items()
		
class HelpSwitcher(ui.View):
	def __init__(self, embeds, logger):
		super().__init__()
		
		for name, embed in embeds.items():
			self.add_item(self.help_button(name, embed))
			
		self.children[0].disabled = True
		
	def help_button(self, name, embed):
		async def switch(interaction):
			for child in self.children:
				child.disabled = child.label == name
	
			await interaction.response.edit_message(embed = embed, view = self)
		
		button = ui.Button(label = name, style = discord.ButtonStyle.primary)
		button.callback = switch
		return button
		
	async def on_timeout(self):
		self.clear_items()