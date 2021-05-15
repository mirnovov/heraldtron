import discord
from discord.ext import commands, tasks
from .. import utils

class RollSort(commands.Cog):
	CHANNEL_TYPES = (
		("Market", "market", "\U0001F4B8"),
		("Artist Gallery", "artist", "\U0001F3A8"),
		("Roll of Arms", "roll", "\U0001F4DC")
	)
	KEYWORDS = tuple(entry[1] for entry in CHANNEL_TYPES)
	CATEGORY_CAP = 50
	
	#TODO:
	#- add channel creation command (not in here)
	#- complete sort method (include archiving there)
	#- maybe ditch sort_all()?
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.update_channels())
		self.sort_all.start()
		
	def cog_unload(self):
		self.sort_all().stop()	
		
	async def update_channels(self):
		await self.bot.wait_until_ready()
		
		async for guild in await self.get_guilds(self.bot.dbc):
			reified = self.bot.get_guild(guild[0])
			if not reified: continue
			
			for category in reified.categories:
				if (cat_type := self.get_type(category)) == -1: continue
				is_archived = self.get_archived(category)
				
				for channel in category.channels:
					owner = await self.get_owner(channel)
					await self.bot.dbc.execute(
						"INSERT INTO roll_channels (discord_id, name, user_id, type, guild_id, archived, never_archive)"\
						" VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(discord_id) DO UPDATE SET user_id = ?, type = ?, archived = ?;",
						(channel.id, channel.name, owner, cat_type, guild[0], is_archived, 0, owner, cat_type, is_archived)
					)
					await self.bot.dbc.commit()
					
		self.bot.logger.info(f"Successfully updated roll channels.")
		
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		if not await self.is_valid(self.bot.dbc, after): return
		
		if before.overwrites.items() != after.overwrites.items():
			await self.bot.dbc.execute(
				"UPDATE roll_channels SET owner = ? WHERE discord_id = ?;",
				(self.get_owner(after), after.id)
			)
			await self.bot.dbc.commit()
			
		if before.category != after.category:
			await self.bot.dbc.execute(
				"UPDATE roll_channels SET archived = ? AND type = ? WHERE discord_id = ?;",
				(self.get_archived(after.category), self.get_type(after.category), after.id)
			)
			await self.bot.dbc.commit()

		if before.name != after.name:
			await self.sort_guild(after.guild)
		
	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		cat_type = self.get_type(channel.category)
		if not await self.is_valid(self.bot.dbc, channel) or cat_type == -1: return
		
		await self.bot.dbc.execute(
			"INSERT INTO roll_channels (discord_id, name, user_id, type, guild_id,"\
			" archived, never_archive) VALUES (?, ?, ?, ?, ?, ?, ?);",
			(
				channel.id, channel.name, await self.get_owner(channel), cat_type, 
				channel.guild.id, self.get_archived(channel.category), 0
			)
		)
		await self.bot.dbc.commit()
		await self.sort_guild(channel.guild)
		
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		await self.bot.dbc.execute(
			"DELETE FROM roll_channels WHERE discord_id = ?;", (channel.id,)
		)
		await self.bot.dbc.commit()
		
	@tasks.loop(hours = 48)
	async def sort_all(self):
		#every so often, sort
		async for guild in await self.get_guilds(self.bot.dbc):
			reified = self.bot.get_guild(guild[0])
			if reified: await self.sort_guild(reified)
		
	async def sort_guild(self, guild):
		#TODO
		self.bot.logger.info(f"Roll channels in {guild.name} sorted.")	
	
	@sort_all.before_loop
	async def wait_before_loop(self):
		await self.bot.wait_until_ready()
		
	@staticmethod
	async def is_valid(dbc, channel):
		if isinstance(channel, discord.CategoryChannel): return False
		
		return await utils.fetchone(
			dbc, "SELECT * FROM guilds WHERE discord_id = ? AND sort_channels = 1", 
			(channel.guild.id,)
		)
		
	@staticmethod
	async def get_guilds(dbc):
		return await dbc.execute("SELECT * FROM guilds WHERE sort_channels = 1")	
	
	@staticmethod	
	def get_type(category):
		name = category.name.lower()
		for i, keyword in enumerate(RollSort.KEYWORDS):
			if keyword in name: return i

		return -1
		
	@staticmethod
	def get_archived(category):
		return int("archived" in category.name.lower())
		
	@staticmethod
	async def get_owner(channel):
		for member, overwrite in channel.overwrites.items():
			if isinstance(member, discord.Role): continue
			elif overwrite.pair()[0].manage_channels: return member.id 
		
		return None
		
def setup(bot):
	bot.add_cog(RollSort(bot))