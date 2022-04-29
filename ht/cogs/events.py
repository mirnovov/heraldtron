import discord, re, sqlite3
from discord.ext import commands
from .. import utils

class BotEvents(commands.Cog, name = "Bot events"):
	FIND_MENTIONS = re.compile(r"(?m)(<(#|@|:\w+:)(\d+)>)")
	FIND_SENTENCES = re.compile(r"(?m)(\w.*?)(\.|\?|\n)")
	THREAD_MAX = 90
	THUMBS_UP = "\U0001F44D"
	THUMBS_DOWN = "\U0001F44E"
	SHRUG = "\U0001F937"
	
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
			"INSERT INTO guilds VALUES (?, ?, ?, ?, ?, ?, ?);",
			(guild.id, guild.name, 0, 0, 1, None, None)
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
				
			self.bot.proposal_cache[message.id] = message
					
		elif not channel[3] or len(message.attachments) < 1: 
			#not oc post or no attachments
			return
			
		if len(title) > self.THREAD_MAX:
			title = title[:self.THREAD_MAX] + "..."
		elif not title:
			time = message.created_at.strftime("%d %B %Y")
			title = f"{message.author.name} on {time}"
				
		await message.create_thread(name = title)
	
	@commands.Cog.listener("on_raw_reaction_add")	
	@commands.Cog.listener("on_raw_reaction_remove")
	async def reaction_update(self, payload):
		if payload.message_id in self.bot.proposal_cache:
			channel = await utils.get_channel(self.bot, payload.channel_id)
			self.bot.proposal_cache[payload.message_id] = await channel.fetch_message(payload.message_id)
		
	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		record = self.bot.channel_cache.get(payload.channel_id)
		if not record or not record[2]: return
		
		#On proposal delete99
		message = self.bot.proposal_cache.get(payload.message_id)
		channel = await utils.get_channel(self.bot, payload.channel_id)
		thread = channel.get_thread(payload.message_id)
		if not message or not thread: return
		
		content = message.content[:200].replace("\n", "\n> ")
		reactions = "  ".join(f"{reaction.emoji} {reaction.count}" for reaction in message.reactions)
		response = f"**Proposal closed**\n> {content}\n\n{reactions}"
		
		await thread.send(response)
		await thread.edit(archived = True)
		
		if log_channel := self.bot.guild_cache[payload.guild_id][1][7]:
			log = await utils.get_channel(self.bot, log_channel)
			await log.send(response + f"\n{thread.mention}")
	
	@commands.Cog.listener()
	async def on_member_join(self, member):
		await self.post_welcome_message(member, False)		
		
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		await self.post_welcome_message(member, True)
		
	async def post_welcome_message(self, member, leave):
		guild_db = await self.bot.dbc.execute_fetchone("SELECT * FROM guilds WHERE discord_id == ?;", (member.guild.id,))
		
		if not guild_db or not guild_db[4]: 
			#if guild not in db (shouldn't happen) or if disabled
			return
			
		if leave: message, emoji = guild_db[6], ":outbox_tray:"
		else: message, emoji = guild_db[5], ":inbox_tray:"
		
		if not message:
			message = f"We're sorry to see you leaving, **MEMBER_NAME**." if leave else f"Welcome to the **GUILD_NAME** server, MENTION."
			
		formatted = self.welcome_fmt(member, message)
		
		await member.guild.system_channel.send(f"{emoji} | {formatted}")
		
	def welcome_fmt(self, member, subst_text):
		if not subst_text: return None
		
		special_vars = {
			"GUILD_NAME": member.guild.name,
			"MEMBER_NAME": f"{member.name}#{member.discriminator}",
			"MENTION": member.mention
		}
		
		for name, value in special_vars.items():
			subst_text = subst_text.replace(name,value)
		
		return subst_text		
		
def setup(bot):
	bot.add_cog(BotEvents(bot))
