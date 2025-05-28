import discord, aiohttp, asyncio, re, typing
from bs4 import BeautifulSoup, Comment
from discord import app_commands
from discord.ext import commands
from .. import converters, embeds, utils

class HeraldryRoll(utils.MeldedCog, name = "Roll of Arms", category = "Heraldry"):
	FIND_HTML_TAGS = re.compile(r"<[^>]*>")
	ROA_FORM = "https://forms.gle/FLVVc8ncQpfhNa7D8"
	NOVOV_GREII_N = 129
	WIKI_URL = "rollofarms.miraheze.org"

	def __init__(self, bot):
		self.bot = bot
		self.context_commands = [
			app_commands.ContextMenu(name = "View arms", callback = self.arms_action),
			app_commands.ContextMenu(name = "View emblazon", callback = self.emblazon_action)
		]
		
		for c in self.context_commands: 
			self.bot.tree.add_command(c)
		
	async def cog_unload(self):
		super().cog_unload()
		
		for c in self.context_commands: 
			self.bot.tree.remove_command(c)
		
	@commands.hybrid_command(
		help = "Looks up an user's coat of arms.\nUses GreiiEquites' Book of Arms as a source,"
			   " and if the user has defined an emblazon using `!setemblazon`, their emblazon.",
		aliases = ("armiger", "greiin", "showarms", "arms")
	)
	@app_commands.describe(user = "The armiger to look up. Defaults to the command sender.")
	async def a(self, ctx, user: converters.Armiger = None):
		user = user or await self.get_author_roll(ctx.author)
		embed = await self.get_arms(user, ctx.clean_prefix, ctx.author)
		
		await ctx.send(embed = embed)
		
	@commands.hybrid_command(
		help = f"Looks up the symbology of a user's coat of arms.\nUses GreiiEquites' https://{WIKI_URL} as a source.",
		aliases = ("s", "symbols")
	)
	@app_commands.describe(user = "The armiger to look up. Defaults to the command sender.")
	@utils.trigger_typing
	async def symbolism(self, ctx, user: converters.Armiger = None):
		user = user or await self.get_author_roll(ctx.author)
		url = f"https://{self.WIKI_URL}/wiki/GreiiN:{user['greii_n']}"

		async with self.bot.session.get(url) as response:
			if response.status == 404:
				raise utils.CustomCommandError(
					f"Armiger is not on {self.WIKI_URL}",
					f"The arms of the armiger are not on the https://{self.WIKI_URL} "
					"website. If you would like to add your arms and related symbolism "
					f"to the website, please fill out the [form here]({self.ROA_FORM})."
				)
			
			soup = BeautifulSoup(await response.text(), "html.parser")
			values = soup.select("h2:has(#Symbolism)")
			
			if not values:
				raise utils.CustomCommandError(
					f"Armiger doesn't have symbolism on {self.WIKI_URL}",
					"The armiger has opted not to include symbolism on the "
					f"https://{self.WIKI_URL} website."
				)
			
			next_section = values[0].next_sibling
			symbolism_text = ""
			while next_section is not None and not isinstance(next_section, Comment) and not str(next_section).startswith("<h"):
				markdown = re.sub(
					self.FIND_HTML_TAGS,
					"",
					str(next_section).replace("<b>", "**").replace("</b>", "**").replace("<i>", "*").replace("</i>", "*")
				)
				symbolism_text += f"{markdown}\n"
				next_section = next_section.next_sibling
				
			symbolism_text = symbolism_text.strip()[:4000]
			
			embed = embeds.GENERIC.create(
				f"Symbolism for {user["qualified_name"]}",
				f"{symbolism_text}\n\n[**See more on {self.WIKI_URL}...**]({url})",
				heading = f"GreiiN:{user["greii_n"]:04}"
			)
			embed.set_footer(text = f"Textual content from https://{self.WIKI_URL} by GreiiEquites.")

			await ctx.send(embed = embed)

	@commands.hybrid_command(help = "Deletes any extant emblazon that you have set.", aliases = ("de",))
	async def delemblazon(self, ctx):
		if not await ctx.bot.dbc.execute_fetchone("SELECT * FROM emblazons WHERE id = ?;", (ctx.author.id,)):
			raise utils.CustomCommandError(
				"User does not have emblazon",
				"You do not have an emblazon to remove."
			)

		await self.bot.dbc.execute("UPDATE emblazons SET url = NULL WHERE id = ?;", (ctx.author.id,))
		await self.bot.dbc.commit()

		await ctx.send(":x: | Emblazon removed.")
		
	@commands.hybrid_command(
		help = "Looks up an user-defined emblazon of a coat of arms.",
		aliases = ("emblazon",)
	)
	@app_commands.describe(user = "The user to look up. Defaults to the command sender. To add an emblazon, use /setemblazon.")
	async def e(self, ctx, user : converters.MemberOrUser = None):
		user = user or ctx.author
		embed = await self.get_emblazon(user)

		await ctx.send(embed = embed)

	@commands.hybrid_command(
		help = "Sets the emblazon of your arms used by this bot.\n"
			   "This can either be an attachment or image URL; "
			   "once set, it is associated with your Discord ID.",
		aliases = ("se",)
	)
	@app_commands.describe(image = "The image to use as your emblazon. This can then be looked up via /e.")
	async def setemblazon(self, ctx, image: discord.Attachment):
		url = image.url

		await self.bot.dbc.execute(
			"INSERT INTO emblazons (id, url) VALUES (?1, ?2) ON CONFLICT(id) DO UPDATE SET url = ?2;",
			(ctx.author.id, url)
		)
		await self.bot.dbc.commit()
		await ctx.send(":white_check_mark: | Emblazon updated.")
		
	async def get_arms(self, user, prefix, author):
		embed = embeds.GENERIC.create(user["qualified_name"], user["blazon"], heading = f"GreiiN:{user["greii_n"]:04}")
		embed.set_footer(text = "Textual content from the Book of Arms by GreiiEquites.")
		
		if user[6]:
			embed.set_thumbnail(url = user["url"])
			embed.set_footer(text = embed.footer.text + " Image specified by user.")
		elif user["discord_id"] == author.id:
			embed.description += f"\n**To set an image, use `{prefix}setemblazon`.**"
		
		records = await self.bot.dbc.execute_fetchall(
			f"SELECT * FROM roll_channels WHERE user_id == ? AND user_id IS NOT NULL;",
			(user["discord_id"],)
		)
		links = [f"- <#{record["discord_id"]}>" for record in records]
		wiki_url = f"https://{self.WIKI_URL}/wiki/GreiiN:{user['greii_n']}"
		
		if user["greii_n"] == self.NOVOV_GREII_N:
			links.append("- **[novov.me \u2197\uFE0E](https://novov.me/projects/heraldry)**")
		
		async with self.bot.session.get(wiki_url) as response:
			if response.status == 200: 
				links.append(f"- **[{self.WIKI_URL} \u2197\uFE0E]({wiki_url})**")
		
		if links:
			embed.add_field(name = "External links", value = "\n".join(links))
		
		return embed

	async def get_author_roll(self, author):
		user = await self.bot.dbc.execute_fetchone(
			"SELECT * FROM armigers_e WHERE discord_id == ?;", (author.id,)
		)
		
		if not user:
			await self.bot.get_cog("Bot tasks").sync_book()
		
			user = await self.bot.dbc.execute_fetchone(
				"SELECT * FROM armigers_e WHERE discord_id == ?;", (author.id,)
			)
			
		if user: return user
		
		raise utils.CustomCommandError(
			"Invalid armiger",
			"There are no arms associated with your user account. "
			"To find those of another user, follow the command with their username."
			"If you wish to register your arms, follow the instructions at the Roll of Arms server."
		)
				
	async def get_emblazon(self, user):
		emblazon = await self.bot.dbc.execute_fetchone("SELECT * FROM emblazons WHERE id == ?;", (user.id,))
		
		if emblazon and emblazon["url"]:
			embed = embeds.GENERIC.create(user, "", heading = "Emblazon")
			embed.set_footer(text = "Design and emblazon respectively the property of the armiger and artist.")
			embed.set_image(url = emblazon["url"])
			
			return embed
		
		else: raise utils.CustomCommandError(
			"User does not have emblazon",
			"The user you entered exists, but has not specified an emblazon."
		)
		
	async def arms_action(self, interaction, user: discord.Member):
		interaction.extras["ephemeral_error"] = True
		
		armiger = await converters.Armiger().transform(interaction, user)
		embed = await self.get_arms(armiger, "/", interaction.user)
		await interaction.response.send_message(embed = embed, ephemeral = True)		
		
	async def emblazon_action(self, interaction, user: discord.Member):
		interaction.extras["ephemeral_error"] = True

		embed = await self.get_emblazon(user)
		await interaction.response.send_message(embed = embed, ephemeral = True)

async def setup(bot):
	await bot.add_cog(HeraldryRoll(bot))
