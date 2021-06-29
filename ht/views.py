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
	
	@ui.button(label = "\u27E8\u27E8", style = discord.ButtonStyle.primary, disabled = True)
	async def first_button(self, button, interaction):
		await self.modify(0, interaction)
	
	@ui.button(label = "\U0001F868", style = discord.ButtonStyle.primary, disabled = True)
	async def prev_button(self, button, interaction):
		await self.modify(self.index - 1, interaction)
		
	@ui.button(label = "?")
	async def random_button(self, button, interaction):
		await self.modify(random.randrange(0, self.size + 1), interaction)
	
	@ui.button(label = "\U0001F86A", style = discord.ButtonStyle.primary)
	async def next_button(self, button, interaction):
		await self.modify(self.index + 1, interaction)
		
	@ui.button(label = "\u27E9\u27E9", style = discord.ButtonStyle.primary)
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