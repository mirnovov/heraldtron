import sqlite3, urllib, logging
from discord.ext import commands, tasks
from .. import utils, embeds

class BotEvents(commands.Cog, name = "Bot Events"):
	def __init__(self, bot):
		self.bot = bot
		self.get_reddit_posts.start()
		
	def cog_unload(self):
		self.get_reddit_posts.stop()
		
	@tasks.loop(hours = 2)
	async def get_reddit_posts(self):
		bot = self.bot
		feeds = await bot.dbc.execute("SELECT * FROM reddit_feeds")
		
		async for feed in feeds:
			query = urllib.parse.quote(feed[4])
			posts = await utils.get_json(
				bot.session,
				f"https://www.reddit.com/r/{feed[3]}/search.json?q={query}&restrict_sr=on&sort=new&limit=8"
			)
			
			if posts.get("error"): 
				logging.getLogger("heraldtron").warning(f"Cannot access Reddit:\n{posts}")
				continue #necessary as reddit can be down
			
			posts = posts["data"]["children"]
			channel = bot.get_channel(feed[2]) or await bot.fetch_channel(feed[2])
			
			if len(posts) == 0: continue
			
			for post in posts:
				post = post["data"]
				if post["name"] == feed[5]: break
				
				desc = "" if not post.get("selftext") else post["selftext"].split("\n#")[0]
				
				embed = embeds.FEED.create(post["title"], desc)
				embed.url = f"https://old.reddit.com{post['permalink']}"
				embed.set_footer(text = f"posted to r/{post['subreddit']} by u/{post['author']}")
				
				if post.get("preview"):
					embed.set_thumbnail(url = post["preview"]["images"][0]["source"]["url"].replace("&amp;","&"))
				
				await channel.send(embed = embed)
			
			if posts[0]["data"]["name"] != feed[5]:	
				await bot.dbc.execute(
					"UPDATE reddit_feeds SET last_post = ? WHERE id = ?", 
					(posts[0]["data"]["name"], feed[0])
				)
				await bot.dbc.commit()
				
	@get_reddit_posts.before_loop
	async def before_reddit_loop(self):
		await self.bot.wait_until_ready()
		
	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		await self.bot.dbc.execute(
			"INSERT INTO guilds VALUES (?, ?, ?, ?, ?, ?);",
			(guild.id, guild.name, 0, 1, None, None)
		)
		await self.bot.dbc.commit()
		
	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		await self.bot.dbc.execute("DELETE FROM guilds WHERE discord_id = ?;",(guild.id,))
		await self.bot.dbc.commit()
	
	@commands.Cog.listener()
	async def on_member_join(self, member):
		await self.post_welcome_message(member, False)		
		
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		await self.post_welcome_message(member, True)
		
	async def post_welcome_message(self, member, leave):
		guild_db = await utils.get_guild_row(self.bot, member.guild.id)
		
		if not guild_db or not guild_db[3]: 
			#if guild not in db (shouldn't happen) or if disabled
			return
			
		if leave: message, emoji = guild_db[5], ":outbox_tray:"
		else: message, emoji = guild_db[4], ":inbox_tray:"
			
		formatted = self.welcome_fmt(member, message or f"We're sorry to see you leaving, **MEMBER_NAME**.")
		
		await member.guild.system_channel.send(f"{emoji} | {formatted}")
		
	def welcome_fmt(self, member, subst_text):
		if not subst_text: return None
		
		special_vars = {
			"GUILD_NAME": member.guild.name,
			"MEMBER_NAME": utils.qualify_name(member),
			"MENTION": member.mention
		}
		
		for name, value in special_vars.items():
			subst_text = subst_text.replace(name,value)
		
		return subst_text		
		
def setup(bot):
	bot.add_cog(BotEvents(bot))