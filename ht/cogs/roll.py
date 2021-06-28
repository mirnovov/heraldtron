import typing
from discord.ext import commands
from .. import converters, embeds, utils

class HeraldryRoll(utils.MeldedCog, name = "Roll of Arms", category = "Heraldry"):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(
		help = "Looks up an user's coat of arms.\nUses GreiiEquites' Book of Arms as a source."
			   " If you type `img` before the user name, also shows a user-selected emblazon, like with `!emblazon`."
			   " This is off by default as Greii eventually aims to implement a consistent emblazon style.",
		aliases = ("a", "greiin", "showarms", "arms")
	)
	async def armiger(self, ctx, user: converters.Armiger = None):
		if not user:
			user = await ctx.bot.dbc.execute_fetchone(
				"SELECT * FROM armigers_e WHERE discord_id == ?;", (ctx.author.id,)
			)
			
			if not user: raise utils.CustomCommandError(
				"Invalid armiger",
				"There are no arms associated with your user account. "
				"To find those of another user, follow the command with their username."
			)
		
		embed = embeds.GENERIC.create(f"{user[2]}#{user[3]:04}", user[4], heading = f"GreiiN:{user[0]:04}")
		embed.set_footer(
			text = "Textual content from the Book of Arms by GreiiEquites. Image specified by user."
		)
		
		if user[6]:
			embed.set_thumbnail(url = user[6])
			
		channels = await ctx.bot.dbc.execute_fetchall(
			"SELECT * FROM roll_channels WHERE user_id == ? AND user_id IS NOT NULL;", 
			(user[1],)
		)
		mentions = []
		
		for record in channels:
			channel = await utils.get_channel(ctx.bot, record[0])
			if not channel: continue
			mentions.append(channel.mention)
			
		if mentions: embed.add_field(name = "Rolls of arms", value = ','.join(mentions))
		
		await ctx.send(embed = embed)
		
	@commands.command(help = "Deletes any extant emblazon that you have set.", aliases = ("de",))
	async def delemblazon(self, ctx):
		if not await ctx.bot.dbc.execute_fetchone("SELECT * FROM emblazons WHERE id = ?;", (ctx.author.id,)): 
			raise utils.CustomCommandError(
				"User does not have emblazon",
				"You do not have an emblazon to remove."
			)
		
		await self.bot.dbc.execute(
			"DELETE FROM emblazons WHERE id = ?;",
			(ctx.author.id,)
		)
		await self.bot.dbc.commit()
		await ctx.send(":x: | Emblazon removed.")
		
	@commands.command(
		help = "Looks up a user-defined emblazon of a coat of arms.",
		aliases = ("e",)
	)
	@utils.trigger_typing
	async def emblazon(self, ctx, user : converters.MemberOrUser = None):
		user = user or ctx.author
		emblazon = await ctx.bot.dbc.execute_fetchone("SELECT * FROM emblazons WHERE id == ?;", (user.id,))
		
		if emblazon: 
			embed = embeds.GENERIC.create(f"{user.name}#{user.discriminator}", "", heading = "Emblazon")
			embed.set_footer(text = "Design and emblazon respectively the property of the armiger and artist.")
			
			embed.set_image(url = emblazon[1])
			
			await ctx.send(embed = embed)
		else: raise utils.CustomCommandError(
			"User does not have emblazon",
			"The user you entered exists, but has not specified an emblazon."
		)
		
	@commands.command(
		help = "Sets the emblazon of your arms shown by `!emblazon`.\n"
			   "This can either be an attachment or image URL; "
			   "once set, it is associated with your Discord ID.",
		aliases = ("se",)
	)
	async def setemblazon(self, ctx, url : typing.Optional[converters.Url] = None):	
		if not url and len(ctx.message.attachments) > 0:
			url = ctx.message.attachments[0].url
		elif not url:
			raise utils.CustomCommandError(
				"No emblazon provided",
				"An image is required to set as the emblazon. "
				"Either attach one or provide an URL."
			)
			
		await self.bot.dbc.execute(
			"INSERT INTO emblazons (id, url) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET url = ?;",
			(ctx.author.id, url, url)
		)
		await self.bot.dbc.commit()
		await ctx.send(":white_check_mark: | Emblazon updated.")
		
def setup(bot):
	bot.add_cog(HeraldryRoll(bot))