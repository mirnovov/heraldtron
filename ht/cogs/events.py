import sqlite3
from discord.ext import commands

class BotEvents(commands.Cog, name = "Bot events"):
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.update_guilds())
		
	async def update_guilds(self):
		await self.bot.wait_until_ready()
		for guild in self.bot.guilds:
			await self.bot.dbc.execute(
				"INSERT OR IGNORE INTO guilds VALUES (?, ?, ?, ?, ?, ?, ?);",
				(guild.id, guild.name, 0, 0, 1, None, None)
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