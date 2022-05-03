import discord, asyncio, uuid
from discord.ext import commands, tasks
from collections import deque
from datetime import datetime, timedelta
from .. import utils

class RollChannels(commands.Cog, name = "Roll Channels"):
	VARIANTS = ["market", "artist", "roll of arms"]
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialise())
		
	async def initialise(self):
		await self.bot.wait_until_ready()
		
		async for guild in await self.bot.dbc.execute("SELECT discord_id FROM guilds WHERE roll = 1"):
			reified = self.bot.get_guild(guild[0])
			if not reified: continue
			
			for category in reified.categories:					
				if not self.valid_category(category): continue
				personal = self.is_personal(category)
							
				for channel in category.channels:					
					owner = await self.get_owner(channel)
					await self.bot.dbc.execute(
						"INSERT INTO roll_channels (discord_id, user_id, guild_id, personal, name) VALUES (?, ?, ?, ?, ?)"
						" ON CONFLICT(discord_id) DO UPDATE SET user_id = ?, name = ?;",
						(channel.id, owner, guild[0], int(personal), channel.name, owner, channel.name)
					)
					await self.bot.dbc.commit()
					
					if personal:
						await self.add_emblazon(channel, owner)
		
		self.bot.logger.info(f"Successfully prepared roll information.")
			
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		if not isinstance(after, discord.TextChannel) or not self.valid_category(after.category): 
			return
		
		if before.overwrites.items() != after.overwrites.items():
			await self.bot.dbc.execute(
				"UPDATE roll_channels SET user_id = ? WHERE discord_id = ?;",
				(await self.get_owner(after), after.id)
			)
			await self.bot.dbc.commit()
		
	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		if not isinstance(channel, discord.TextChannel) or not self.valid_category(channel.category):
			return
			
		await self.bot.dbc.execute(
			"INSERT INTO roll_channels (discord_id, user_id, guild_id, personal, name) VALUES (?, ?, ?, ?, ?);",
			(channel.id, await self.get_owner(channel), channel.guild.id, self.is_personal(channel.category), channel.name)
		)
		await self.bot.dbc.commit()
		
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		await self.bot.dbc.execute(
			"DELETE FROM roll_channels WHERE discord_id = ?;", (channel.id,)
		)
		await self.bot.dbc.commit()
		
	async def add_emblazon(self, channel, owner):
		if await self.bot.dbc.execute_fetchone("SELECT * FROM emblazons WHERE id == ?", (owner,)):
			return #has emblazon
		
		pinned = list(filter(
			lambda p: len(p.attachments) > 0, await channel.pins()
		)).reverse()
		
		if not pinned or not owner: return
		
		await self.bot.dbc.execute(
			"INSERT INTO emblazons (id, url) VALUES (?, ?) ON CONFLICT DO NOTHING;",
			(owner, url)
		)
		await self.bot.dbc.commit()

	@staticmethod
	async def get_owner(channel):
		for member, overwrite in channel.overwrites.items():
			if isinstance(member, discord.Role): continue
			elif overwrite.pair()[0].manage_channels: return member.id 
		return None
		
	def valid_category(self, category):
		if category.guild.id not in {
			id: g[0] for (id, g) in self.bot.guild_cache.items() if g[1][3]
		}:
			return False
		
		name = category.name.lower()
		
		for v in RollChannels.VARIANTS:
			if v in name: return True
				
		return False
		
	def is_personal(self, category):
		return self.VARIANTS[2] in category.name.lower()
		
def setup(bot):
	bot.add_cog(RollChannels(bot))
