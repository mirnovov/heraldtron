import discord, asyncio, uuid
from discord.ext import commands, tasks
from collections import deque
from datetime import datetime, timedelta
from .. import utils

class RollChannels(commands.Cog, name = "Roll Sorting"):
	VARIANTS = ["Market", "Artist Gallery", "Roll of Arms"]
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialise())
		#archive is started in initialise()
		
	def cog_unload(self):
		self.archive.stop()
		
	async def initialise(self):
		await self.bot.wait_until_ready()
		
		async for guild in await self.bot.dbc.execute("SELECT discord_id FROM guilds WHERE roll = 1"):
			if not (reified := self.bot.get_guild(guild[0])): continue
			
			for category in reified.categories:				
				for channel in category.channels:
					owner = await self.get_owner(channel)
					await self.bot.dbc.execute(
						"INSERT INTO roll_channels (discord_id, user_id, guild_id) VALUES (?, ?, ?)"
						" ON CONFLICT(discord_id) DO UPDATE SET user_id = ?;",
						(channel.id, owner, guild[0], owner)
					)
					await self.bot.dbc.commit()
		
		self.bot.logger.info(f"Successfully prepared roll information.")
			
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		if not self.is_roll(after): return
		
		if before.overwrites.items() != after.overwrites.items():
			await self.bot.dbc.execute(
				"UPDATE roll_channels SET user_id = ? WHERE discord_id = ?;",
				(await self.get_owner(after), after.id)
			)
			await self.bot.dbc.commit()
		
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
		await self.bot.dbc.execute(
			"DELETE FROM roll_channels WHERE discord_id = ?;", (channel.id,)
		)

	@staticmethod
	async def get_owner(channel):
		for member, overwrite in channel.overwrites.items():
			if isinstance(member, discord.Role): continue
			elif overwrite.pair()[0].manage_channels: return member.id 
		return None
		
	def is_roll(self, channel):
		if not isinstance(channel, discord.TextChannel): 
			return False
		
		return channel.guild.id in self.roll_guilds()
	
	@staticmethod	
	def is_roll_channel(category):
		name = category.name.lower()
		
		for v in RollSort.VARIANTS:
			if v in name: return True
				
		return None
		
	def roll_guilds(self):
		return {id: g[0] for (id, g) in self.bot.guild_cache.items() if g[1][3]}
		
def setup(bot):
	bot.add_cog(RollChannels(bot))
