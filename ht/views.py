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