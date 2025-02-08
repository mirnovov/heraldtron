import discord, asyncio, json, random, re
from thefuzz import process
from discord import app_commands
from discord.ext import commands
from .. import embeds, utils, views

class HeraldryResources(utils.MeldedCog, name = "Resources", category = "Heraldry"):
	PAGE_SIZE = 8

	def __init__(self, bot):
		self.bot = bot
		self.resources = {}
		self.bot.loop.create_task(self.load_resources())

	def add_resource(self, data):
		image = data.get("image", False)
		embed = embeds.GENERIC.create(data["title"], data["desc"], heading = "Resource")
		
		if not image: embed.url = data["href"]
		else: embed.set_image(url = data["href"])

		@commands.command(name = data["id"], help = data["desc"], cog = self, hidden = True)
		async def resource_command(ctx):
			embed.set_footer(text = f"Use {ctx.clean_prefix}resources to view a list of all resources.")
			await ctx.send(embed = embed)

		app_command_id = discord.utils.remove_markdown(data["title"])

		self.resources[app_command_id] = { 
			**data, "app_command_id": app_command_id, "command": resource_command, "embed": embed 
		}
		self.bot.add_command(resource_command)

	async def load_resources(self):
		with open("data/resources.json") as file:
			data = json.load(file)

		for resource in data:
			self.add_resource(resource)

		self.__cog_commands__ += tuple(v["command"] for v in self.resources.values())			
		self.bot.logger.info("Successfully loaded resources.")
		
	@commands.hybrid_command(
		help = "Displays a random heraldic resource.",
		aliases = ("rr", "randomresource")
	)
	async def randresource(self, ctx):
		command = random.choice(self.resource_commands)
		await command.callback(ctx)

	@commands.hybrid_command(
		help = "Lists all resource commands.",
		aliases = ("re", "source", "resource", "r")
	)
	async def resources(self, ctx):
		pages = []
		current_size = self.PAGE_SIZE + 1

		for resource in self.resources.values():
			if current_size > self.PAGE_SIZE:
				embed = embeds.GENERIC.create(
					"All resources", "", heading = "Heraldic resources collection"
				)
				embed.set_footer(
					text = "Use the commands listed here to fetch resources individually for quick reference."
				)
				
				pages.append(embed)
				current_size = 0
				
			if ctx.interaction: full_command = f"`/r name: {resource['app_command_id']}`\n"
			else: full_command = f"`{ctx.clean_prefix}{resource['id']}` - "

			embed.add_field(
				name = resource["title"],
				value = f"{full_command}{resource['desc']} [**View**]({resource['href']})",
				inline = False
			)
			
			current_size += 1

		await views.Navigator(ctx, pages).run()
		
	@app_commands.command(description = "Fetches a heraldic resource.")
	@app_commands.describe(name = "The name of the resource to fetch. A detailed list can be viewed at /resources")
	async def r(self, interaction, name: str):
		if name not in self.resources:
			name, score = process.extractOne(name, list(self.resources.keys()))
			
			if score < 30:
				raise utils.CustomCommandError(
					"Invalid resource",
					f"The resource `{name}` does not exist. Check that you spelled it correctly."
				)
			
		embed = self.resources[name]["embed"]
		embed.set_footer(text = f"Use /resources to view a list of all resources.")
		
		await interaction.response.send_message(embed = embed) 
	
	@r.autocomplete("name")
	async def r_autocomplete(self, interaction, current): 
		if not current or current.isspace():
			matches = [(i, 0) for i in list(self.resources.keys())[:25]]
		else:
			matches = process.extract(current, self.resources.keys(), limit = 25)
		
		return [app_commands.Choice(name = n, value = n) for n, _ in matches]

async def setup(bot):
	await bot.add_cog(HeraldryResources(bot))
