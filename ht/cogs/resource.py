import asyncio, random, csv, re
from discord.ext import commands
from .. import embeds, utils, views

class HeraldryResources(utils.MeldedCog, name = "Resources", category = "Heraldry"):
	RESOURCE = re.compile("(?s)<li.*?data-key=\"(.+?)\">.*?<a href=\"(.+?)\">(.+?)</a>.*?<p>(.+?)</p>")
	RES_SUB_A = re.compile("<i>|</i>")
	RES_SUB_B = re.compile("<[^<]+?>")
	PAGE_SIZE = 8

	def __init__(self, bot):
		self.bot = bot
		self.resources = []
		self.bot.loop.create_task(self.load_resources())

	def add_resource(self, shortname, name, desc, url, image):
		image = int(image)

		@commands.command(name = shortname, help = desc, cog = self, hidden = True)
		async def resource_command(ctx):
			embed = embeds.GENERIC.create(name, desc, heading = "Resource")

			if not image: embed.url = url
			else: embed.set_image(url = url)

			embed.set_footer(text = "Use !resources to view a list of all resources.")
			await ctx.send(embed = embed)

		self.resources.append((resource_command, name, url))

	async def load_resources(self):
		html = await utils.get_text(
			self.bot.session,
			"https://novov.me/linkroll/resources.html?bot",
			encoding = "UTF-8"
		)
		results = await self.bot.loop.run_in_executor(None, re.findall, self.RESOURCE, html)

		for resource in results:
			self.add_resource(
				resource[0],
				re.sub(self.RES_SUB_A, "*", resource[2]),
				re.sub(self.RES_SUB_B, "", resource[3]),
				resource[1],
				0
			)

		with open("data/resources.csv") as file:
			supplementary = list(csv.reader(file, delimiter = ";"))

			for resource in supplementary:
				self.add_resource(*resource)

		self.resource_commands = tuple(resource[0] for resource in self.resources)

		self.__cog_commands__ += self.resource_commands
		for command in self.resource_commands:
			self.bot.add_command(command)

		self.bot.logger.info("Successfully loaded resources.")

	@commands.command(
		help = "Displays a random heraldic resource.",
		aliases = ("rr", "randomresource")
	)
	async def randresource(self, ctx):
		command = random.choice(self.resource_commands)
		await command.callback(ctx)

	@commands.command(
		help = "Lists all resource commands.",
		aliases = ("re", "source", "resource", "r")
	)
	async def resources(self, ctx):
		pages = []
		current_size = self.PAGE_SIZE + 1

		for command, name, url in self.resources:
			if current_size > self.PAGE_SIZE:
				embed = embeds.GENERIC.create(
					"All resources", "", heading = "Heraldic resources collection"
				)
				pages.append(embed)
				current_size = 0

			embed.add_field(
				name = name,
				value = f"`{ctx.clean_prefix}{command.name}` - {command.help} [\u2139\uFE0E]({url})",
				inline = False
			)
			current_size += 1

		await views.Navigator(ctx, pages).run()

async def setup(bot):
	await bot.add_cog(HeraldryResources(bot))
