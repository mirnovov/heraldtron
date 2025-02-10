import discord, asyncio, os, uuid
from discord import app_commands
from discord.ext import commands, tasks
from collections import deque
from datetime import datetime, timedelta
from .. import converters, utils

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
						"INSERT INTO roll_channels (discord_id, user_id, guild_id, personal, name) VALUES (?1, ?2, ?3, ?4, ?5)"
						" ON CONFLICT(discord_id) DO UPDATE SET user_id = ?2, name = ?5 WHERE ?2 IS NOT NULL;",
						(channel.id, owner, guild["discord_id"], int(personal), channel.name)
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
				"UPDATE roll_channels SET user_id = ?1 WHERE discord_id = ?2;",
				(await self.get_owner(after), after.id)
			)
			await self.bot.dbc.commit()

	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		if not isinstance(channel, discord.TextChannel) or not self.valid_category(channel.category):
			return

		await self.bot.dbc.execute(
			"INSERT INTO roll_channels (discord_id, user_id, guild_id, personal, name) VALUES (?1, ?2, ?3, ?4, ?5);",
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
			"INSERT INTO emblazons (id, url) VALUES (?1, ?2) ON CONFLICT DO NOTHING;",
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
		if category.guild.id not in [
			id for (id, g) in self.bot.guild_cache.items() if g[1]["roll"]
		]:
			return False

		name = category.name.lower()

		for v in RollChannels.VARIANTS:
			if v in name: return True

		return False

	def is_personal(self, category):
		return self.VARIANTS[2] in category.name.lower()
	
	@app_commands.describe(
		origin = "The channel to be transferred.", 
		target = "The target channel. A thread will be created with the original channel's name."
	)
	@app_commands.default_permissions(manage_channels = True)
	@app_commands.command(description = "Transfer the contents of a channel to a thread.")
	async def rollarchive(self, interaction, origin: discord.TextChannel, target: discord.TextChannel):
		thread = await target.create_thread(
			name = origin.name,
			type = discord.ChannelType.public_thread
		)
		await interaction.response.defer(ephemeral = True)
		
		async for message in origin.history(limit = None, oldest_first = True):
			embed, picture = await self.to_embed(message)
			
			try:
				await thread.send(embed = embed, file = picture)
			except:
				embed.description += "\n**Picture could not send**"
				await thread.send(embed = embed)
			
			await asyncio.sleep(0.5)
		
		await interaction.followup.send(":white_check_mark: | Channel archived successfully.")
	
	
	@app_commands.describe(
		origin = "The thread to be transferred. This will need to be unarchived.", 
		target = "The target channel. Note that this doesn't set up permissions for anyone to post in it."
	)
	@app_commands.default_permissions(manage_channels = True)
	@app_commands.command(description = "Transfer the contents of a thread to a channel.")
	async def rollunarchive(self, interaction, origin: converters.ArchivedThread, target: discord.TextChannel):
		await interaction.response.defer(ephemeral = True)

		async for message in origin.history(limit = None, oldest_first = True):
			embed = message.embeds[0]
			picture = None
			
			if not embed: 
				embed, picture = await self.to_embed(message)
			else:
				if len(message.attachments) > 0:
					picture = await message.attachments[0].to_file()
					embed.set_image(url = f"attachment://{picture.filename}")
			
			await target.send(embed = embed, file = picture)
		
		await interaction.followup.send(":white_check_mark: | Channel unarchived successfully.")
		
	@staticmethod 
	async def to_embed(message):
		embed = discord.Embed(description = message.content[:1880])
		embed.set_footer(text = 
			f"{message.author.global_name}"
			f" on {message.created_at.strftime('%d %b %y')}"
		)
		picture = None
		
		if len(message.attachments) > 0:
			picture = await message.attachments[0].to_file()
			embed.set_image(url = f"attachment://{picture.filename}")
		
		return embed, picture
		
	@staticmethod 
	def get_name(message):
		embed = message.embeds[0]
		
		if embed: return embed.footer.text.split(" on ")[0]
		else: return message.author.name

async def setup(bot):
	await bot.add_cog(RollChannels(bot))
