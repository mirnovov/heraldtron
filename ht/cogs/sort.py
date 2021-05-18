import discord, asyncio, uuid, itertools
from discord.ext import commands, tasks
from collections import deque
from .. import utils

class RollSort(commands.Cog):
	VARIANTS = (
		("Market", "market", "\U0001F4B8"),
		("Artist Gallery", "artist", "\U0001F3A8"),
		("Roll of Arms", "roll", "\U0001F4DC")
	)
	LIMIT = 46
	
	#TODO:
	#- add channel creation command (not in here)
	#- add archiving method
	
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
				for channel in category.channels:
					owner = await self.get_owner(channel)
					await self.bot.dbc.execute(
						"INSERT INTO roll_channels (discord_id, user_id, guild_id) VALUES (?, ?, ?)"\
						" ON CONFLICT(discord_id) DO UPDATE SET user_id = ?;",
						(channel.id, owner, guild[0], owner)
					)
					await self.bot.dbc.commit()
					
		self.bot.logger.info(f"Successfully updated roll channel information.")
		
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		if not await self.is_valid(self.bot.dbc, after): return
		
		if before.overwrites.items() != after.overwrites.items():
			await self.bot.dbc.execute(
				"UPDATE roll_channels SET owner = ? WHERE discord_id = ?;",
				(self.get_owner(after), after.id)
			)
			await self.bot.dbc.commit()

		if before.name != after.name:
			cat = after.category
			await self.sort(channel.guild, self.get_variant(cat), self.get_archived(cat))
		
	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		if not await self.is_valid(self.bot.dbc, channel) or not (variant := self.get_variant(channel.category)):
			return
			
		await self.bot.dbc.execute(
			"INSERT INTO roll_channels (discord_id, user_id, guild_id) VALUES (?, ?, ?);",
			(channel.id, await self.get_owner(channel), channel.guild.id)
		)
		await self.bot.dbc.commit()
		await self.sort(channel.guild, variant, self.get_archived(channel.category))
		
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		if isinstance(channel, discord.CategoryChannel): return 
		await self.bot.dbc.execute(
			"DELETE FROM roll_channels WHERE discord_id = ?;", (channel.id,)
		)
		await self.sort(channel.guild, self.get_variant(channel.category), self.get_archived(channel.category))
		
	@tasks.loop(hours = 48)
	async def sort_all(self):
		async for guild in await self.get_guilds(self.bot.dbc):
			reified = self.bot.get_guild(guild[0])
			if not reified: continue
			
			for archived, variant in ((int(a), v) for a in (0, 1) for v in RollSort.VARIANTS):
				await self.sort(reified, variant, archived)
				
			self.bot.logger.info(f"All channels have been sorted.")
		
	async def sort(self, guild, variant, archived):		
		def chunkize(array):
			#Sort and divide into subarrays of LIMIT size, then reverse the outer list
			array = tuple(sorted(array, key = lambda ch: ch.name))
			for n in reversed(range(0, len(array), RollSort.LIMIT)):
				yield tuple(array[n:n + RollSort.LIMIT])
		
		categories = deque(self.get_categories(guild, variant, archived))
		if len(categories) == 0: return
		
		chunks = tuple(chunkize(chn for cat in categories for chn in cat.channels))
		diff = len(chunks) - len(categories)
		prefix = f"{variant[2]} {variant[0]}" if not archived else f"\U0001F3DB {variant[0]} Archives"
		payload = []
		
		for i, chunk in enumerate(chunks): 
			if i < diff: 
				#create new category, except first since it's in reverse
				category = await guild.create_category(str(uuid.uuid4()), position = categories[-1].position)
				await asyncio.sleep(1)
			else:
				category = categories.pop()
			
			for pos, channel in enumerate(chunk):
				if channel.position != pos:
					payload.append({"id": channel.id, "position": pos})
					
				if channel.category_id != category.id:
					await channel.edit(category = category)
					await asyncio.sleep(1)
					
			name = f"{prefix} ({chunk[0].name[0]}-{chunk[-1].name[0]})" 
			if category.name != name: await category.edit(name = name)
			
		asyncio.gather(*(cat.delete() for cat in categories)) #delete unused
		
		await self.bot.http.bulk_channel_update(guild.id, payload)
			
	
	@sort_all.before_loop
	async def wait_before_loop(self):
		await self.bot.wait_until_ready()
		
	@staticmethod
	async def get_guilds(dbc):
		return await dbc.execute("SELECT * FROM guilds WHERE sort_channels = 1")	
	
	@staticmethod	
	def get_variant(category):
		name = category.name.lower()
		for variant in RollSort.VARIANTS:
			if variant[2] in name: return variant
		return None
		
	@staticmethod
	def get_archived(category):
		return int("archive" in category.name.lower())
	
	@staticmethod
	async def get_owner(channel):
		for member, overwrite in channel.overwrites.items():
			if isinstance(member, discord.Role): continue
			elif overwrite.pair()[0].manage_channels: return member.id 
		
		return None
		
	async def is_valid(self, dbc, channel):
		if isinstance(channel, discord.CategoryChannel): 
			return False
		
		return await utils.fetchone(
			dbc, "SELECT * FROM guilds WHERE sort_channels = 1 AND discord_id = ?;", 
			(channel.guild.id,)
		)
		
	def get_categories(self, guild, variant, archived):
		for category in guild.categories:
			if self.get_variant(category) == variant and self.get_archived(category) == archived:
				 yield category
		
def setup(bot):
	bot.add_cog(RollSort(bot))