import discord, re, sqlite3, time
from discord.ext import commands, tasks
from .. import embeds, utils

class GuildEvents(commands.Cog, name = "Guild events"):
	FIND_MENTIONS = re.compile(r"(?m)(<(#|@|:\w+:)(\d+)>)")
	FIND_SENTENCES = re.compile(r"(?m)(\w.*?)(\.|\?|\n)")
	THREAD_MAX = 90

	THUMBS_UP = "\U0001F44D"
	THUMBS_DOWN = "\U0001F44E"
	SHRUG = "\U0001F937"
	
	REACT_RATE_LIMIT = 300 #5 minutes

	def __init__(self, bot):
		self.bot = bot		
		self.bot.loop.create_task(self.update_guilds())
	
	async def update_guilds(self):
		await self.bot.wait_until_ready()
		
		for guild in self.bot.guilds:
			if guild.id == self.bot.HERALDRY_GUILD:
				#in heraldry server, so can use custom reacts
				self.THUMBS_UP = "<:a_thumbs_up:961787184891973672>"
				self.THUMBS_DOWN = "<:a_thumbs_down:961787184489316386>"
		
			await self.bot.dbc.execute(
				"INSERT OR IGNORE INTO guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
				(guild.id, guild.name, 0, 0, 1, None, None, 0)
			)
			await self.bot.dbc.commit()
			
	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		await self.bot.dbc.execute(
			"INSERT INTO guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
			(guild.id, guild.name, 0, 0, 1, None, None, 0)
		)
		await self.bot.dbc.commit()
		await self.bot.refresh_cache_guild(guild.id)
	
	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		await self.bot.dbc.execute("DELETE FROM guilds WHERE discord_id = ?;",(guild.id,))
		await self.bot.dbc.commit()
		del self.bot.guild_cache[guild.id]
			
	@commands.Cog.listener()
	async def on_message(self, message):
		if message.channel.id not in self.bot.channel_cache: return
	
		channel = self.bot.channel_cache[message.channel.id]
		title = message.content
	
		for match in re.findall(self.FIND_MENTIONS, message.content):
			#replace mentions and emojis
	
			if match[1][0] == ":": #emoji
				result = match[1][1:-1]
			else: #user or channel mention
				lookup = utils.get_channel if match[1] == "#" else utils.get_user
				id = int(match[2])
				result = (await lookup(self.bot, id)).name
	
			title = title.replace(match[0], result, 1)
	
		title = discord.utils.escape_markdown(title)
	
		if channel[2]:
			#proposal post
			await message.add_reaction(self.THUMBS_UP)
			await message.add_reaction(self.THUMBS_DOWN)
			await message.add_reaction(self.SHRUG)
	
			if match := re.search(self.FIND_SENTENCES, title):
				title = match.group(1)
			
			self.bot.proposal_cache[message.id] = (message, time.time())
	
		elif not channel[3] or len(message.attachments) < 1:
			#not oc post or no attachments
			return
	
		if len(title) > self.THREAD_MAX:
			title = title[:self.THREAD_MAX] + "..."
		elif not title:
			creation = message.created_at.strftime("%d %B %Y")
			title = f"{message.author.name} on {creation}"
	
		await message.create_thread(name = title)
	
	@commands.Cog.listener("on_raw_reaction_add")
	@commands.Cog.listener("on_raw_reaction_remove")
	async def reaction_update(self, payload):
		if payload.message_id not in self.bot.proposal_cache: return
		
		channel = await utils.get_channel(self.bot, payload.channel_id)
		update_time = self.bot.proposal_cache[payload.message_id][1]
		
		if update_time < time.time() + self.REACT_RATE_LIMIT: 
			return
		
		self.bot.proposal_cache[payload.message_id] = (
			await channel.fetch_message(payload.message_id),
			time.time()
		)
	
	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		record = self.bot.channel_cache.get(payload.channel_id)
		if not record or not record[2]: return
	
		#On proposal deletion
		message = self.bot.proposal_cache.get(payload.message_id)[0]
		channel = await utils.get_channel(self.bot, payload.channel_id)
		thread = channel.get_thread(payload.message_id)
		
		if not thread:
			#works for archived threads and returns a thread object, according to Danny
			#should be documented though...
			thread = await self.bot.fetch_channel(payload.message_id)
	
		reactions = "\u3000".join(f"{reaction.emoji} {reaction.count}" for reaction in message.reactions)
		quote = message.content[:400].replace("\n", "\n> ")
		embed = embeds.PROPOSAL.create("", f"> {quote}\n\n{reactions}")
		embed.set_footer(
			text = f"Original post by {message.author}",
			icon_url = message.author.display_avatar.with_size(256).url
		)
	
		await thread.send(embed = embed)
		await thread.edit(archived = True)
	
		if log_channel := self.bot.guild_cache[payload.guild_id][1][7]:
			log = await utils.get_channel(self.bot, log_channel)
			await log.send(embed = embed)

	
async def setup(bot):
	await bot.add_cog(GuildEvents(bot))
