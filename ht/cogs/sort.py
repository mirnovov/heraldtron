import discord, asyncio, uuid
from discord.ext import commands, tasks
from collections import deque
from datetime import datetime, timedelta
from .. import utils

class RollSort(commands.Cog, name = "Roll Sorting"):
	VARIANTS = (
		("Market", "market", "\U0001F4B8"),
		("Artist Gallery", "artist", "\U0001F3A8"),
		("Roll of Arms", "roll", "\U0001F4DC")
	)
	LIMIT = 46
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialise())
		#archive is started in initialise()
		
	def cog_unload(self):
		self.archive.stop()
		
	async def initialise(self):
		await self.bot.wait_until_ready()
		
		async for guild in await self.bot.dbc.execute("SELECT discord_id FROM guilds WHERE sort_channels = 1"):
			if not (reified := self.bot.get_guild(guild[0])): continue
			
			for category in reified.categories:				
				for channel in category.channels:
					owner = await self.get_owner(channel)
					await self.bot.dbc.execute(
						"INSERT INTO roll_channels (discord_id, user_id, guild_id) VALUES (?, ?, ?)"\
						" ON CONFLICT(discord_id) DO UPDATE SET user_id = ?;",
						(channel.id, owner, guild[0], owner)
					)
					await self.bot.dbc.commit()
		
		await self.refresh_cache()	
		self.archive.start()		
		self.bot.logger.info(f"Successfully prepared roll information.")
		
	async def refresh_cache(self):
		self.valid_guilds = {}
		
		async for guild in await self.bot.dbc.execute("SELECT discord_id FROM guilds WHERE sort_channels = 1"):
			reference = await utils.get_guild(self.bot, guild[0])
			if reference:
				self.valid_guilds[guild[0]] = reference
		
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		if not self.is_roll(after): return
		
		if before.overwrites.items() != after.overwrites.items():
			await self.bot.dbc.execute(
				"UPDATE roll_channels SET owner = ? WHERE discord_id = ?;",
				(await self.get_owner(after), after.id)
			)
			await self.bot.dbc.commit()

		if before.name != after.name:
			info = self.get_info(after.category)
			if info: await self.sort(channel.guild, info)
		
	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		if not self.is_roll(channel) or not (info := self.get_info(channel.category)):
			return
			
		await self.bot.dbc.execute(
			"INSERT INTO roll_channels (discord_id, user_id, guild_id) VALUES (?, ?, ?);",
			(channel.id, await self.get_owner(channel), channel.guild.id)
		)
		await self.bot.dbc.commit()
		await self.sort(channel.guild, info)
		
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		if not self.is_roll(channel): return
		await self.bot.dbc.execute(
			"DELETE FROM roll_channels WHERE discord_id = ?;", (channel.id,)
		)
		info = self.get_info(channel.category)
		if info: await self.sort(channel.guild, info	)
		
	@commands.Cog.listener()
	async def on_message(self, message):
		if not self.is_roll(message.channel): return
		
		info = self.get_info(message.channel.category)
		
		if info and info[3]:
			info = (*info[:3], False)
			await message.channel.edit(category = self.get_last_category(message.guild, info))
			await self.sort(message.guild, info)
	
	@tasks.loop(hours = 48)
	async def archive(self):
		for id, guild in self.valid_guilds.items():
			to_sort = set()
			
			for category in guild.categories:
				info = self.get_info(category)
				if not info or info[3]: continue
				
				for channel in category.text_channels:	
					message = channel.last_message_id
					last = await channel.fetch_message(message) if message else channel
					year_ago = datetime.now() - timedelta(days = 365)
					
					if last.created_at < year_ago: 	
						info = (*info[:3], True)
						await channel.edit(category = self.get_last_category(guild, info))
						to_sort.add(info)
					
			for variant in to_sort:
				await self.sort(guild, info)
		
		self.bot.logger.info(f"All channels have been checked for archiving.")
	
	async def sort_all(self):
		#not ever called, only exists for debugging	
		for id, guild in self.valid_guilds.items():			
			for info in ((*v, a) for a in (False, True) for v in RollSort.VARIANTS):
				await self.sort(guild, info)
				
			self.bot.logger.info(f"All channels have been sorted.")
		
	async def sort(self, guild, info):
		def chunkise(array):
			#Sort and divide into subarrays of LIMIT size, then reverse the outer list
			array, result = tuple(sorted(array, key = lambda ch: ch.name)), []
			
			for n in reversed(range(0, len(array), RollSort.LIMIT)):
				result.append(tuple(array[n:n + RollSort.LIMIT]))
			
			return result
		
		categories = deque(self.get_categories(guild, info))
		chunks = chunkise(chn for cat in categories for chn in cat.channels)
		diff = len(chunks) - len(categories)
		prefix = f"{info[2]} {info[0]}" if not info[3] else f"\U0001F3DB {info[0]} Archives"
		payload = []
		
		if len(categories) == 0: return
		
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
	
	@staticmethod
	async def get_owner(channel):
		for member, overwrite in channel.overwrites.items():
			if isinstance(member, discord.Role): continue
			elif overwrite.pair()[0].manage_channels: return member.id 
		return None
	
	def is_roll(self, channel):
		if isinstance(channel, discord.CategoryChannel): 
			return False
		
		return channel.guild.id in self.valid_guilds
		
	def get_info(self, category):
		name = category.name.lower()
		
		for v in RollSort.VARIANTS:
			if v[1] in name: 
				variant = v
				break
				
		else: return None
		
		return (*variant, "archive" in category.name.lower())	
		
	def get_categories(self, guild, info):
		for category in guild.categories:
			if self.get_info(category) == info: yield category
			
	def get_last_category(self, guild, info):
		return tuple(self.get_categories(guild, info))[-1]
		
def setup(bot):
	bot.add_cog(RollSort(bot))