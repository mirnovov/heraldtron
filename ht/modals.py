import discord, json, random
from discord import ui
from discord.ext import commands
from . import embeds, utils, views

class NvModal(ui.Modal):
	BUTTON_TEXT = "Generate"
	
	async def on_error(self, interaction, error):
		errors = interaction.client.cogs.get("Bot Errors")
		
		if not errors:
			await interaction.response.send_message("An error has been encountered.")
			
		await errors.on_app_command_error(interaction, error)

class GeneratorModal(NvModal, title = "Generate arms"):
	TINCT_AREAS = ("field", "background", "foreground")
	CHART_URL = "https://www.dropbox.com/scl/fo/7lwt17c24vpi4i4x9qj1a/ACQx4VjfTYTU-luVZZ83yak?preview=Generator+by+Snak+and+James.png&rlkey=wrm01mvgi1acnr6yzf3gfctfz"

	short_date = ui.TextInput(
		label = "Enter a day and short month",
		placeholder = "e.g. 8 Apr",
		min_length = 3,
		max_length = 7
	)
	
	first_name = ui.TextInput(
		label = "... and a first name",
		placeholder = "e.g. Jane",
		min_length = 3,
		max_length = 30
	)
	
	last_name = ui.TextInput(
		label = "... and a last name",
		placeholder = "e.g. Smith",
		min_length = 3,
		max_length = 30
	)
	
	@staticmethod
	def get_letter_val(letter, category):
		for letters, value in category.items():
			if letter.upper() in letters: return value
		
		raise utils.BadMessageResponse("Invalid value")
	
	async def on_submit(self, interaction):
		with open("data/generator.json") as file:
			parts = json.load(file)
		
		if self.short_date.value not in parts["charge"].keys():
			raise utils.CustomCommandError(
				"Invalid date",
				f"`{self.short_date.value}` is an invalid date. Enter it as a short date and month, e.g. `8 Apr`"
			)
		
		results = {
			"charge": parts["charge"][self.short_date.value],
			"ordinary": self.get_letter_val(self.first_name.value[0], parts["ordinary"])
		}		
		
		if len(self.last_name.value) % 2 == 0: tinct_types = ("colour", "metal", "colour")
		else: tinct_types = ("metal", "colour", "metal")

		pos = -1
		source = self.last_name.value

		for i, tinct_type, tinct_area in zip(range(3), tinct_types, self.TINCT_AREAS):
			if i == 2:
				pos = 0
				source = self.first_name.value[::-1]
			else:
				pos += 1
			
			if tinct_type == "colour":
				adjacent = pos + 1
				
				if source[pos + 1] == source[pos]:
					tinct_type = "fur"
					pos += 1
					
			results[tinct_area] = self.get_letter_val(source[pos], parts[tinct_type])
		
		embed = embeds.GENERIC.create(
			"", f"-# Generator based on a [chart]({self.CHART_URL}) by Snak and James", heading = "Generated blazon"
		)
		embed.title = f"*{results['field'].capitalize()}, on {utils.pronounise(results['ordinary'])}"\
					  f" {results['background']} {utils.pronounise(results['charge'].lower())}"\
					  f" {results['foreground']}*"
		
		await interaction.response.send_message(embed = embed)

class DistributionModal(NvModal, title = "Enter competitors"):
	names = None
	competitors = ui.TextInput(
		label = "Competitors",
		placeholder = 
			"Enter the competitors. This can either be a simple number or"
			" a list of names, with one on each line.",
		style = discord.TextStyle.long
	)
	
	async def on_submit(self, interaction):
		if parsed_value := int(self.competitors.value):
			self.names = None
			self.size = parsed_value + 1
		else:
			self.names = dict(enumerate(self.competitors.value.split("\n"), start = 1))
			self.size = len(self.names) + 1
			
		if self.size not in range(3, 50):
			raise utils.CustomCommandError(
				"Distribution outside of range",
				"The distribution must have between 3 and 50 members."
			)
			
		await self.respond(None, interaction)
		
	def distribute(self):
		vals = list(range(1, self.size))
		candidates = {i: None for i in range(1, self.size)}
		
		for c in candidates:
			same = c in vals
		
			if len(vals) == 1 and same: #try again, no valid option
				candidates = self.distribute()
				break
			elif same: vals.remove(c)
		
			candidates[c] = vals.pop(random.randrange(0, len(vals)))
			if same: vals.append(c)
		
		return candidates
		
	async def respond(self, ctx, interaction):
		dist = self.distribute()
		output = "".join(
			f"{self.display(k)} \U0001F86A {self.display(v)}\n" 
			for k, v in dist.items()
		)
		
		if ctx: await ctx.send(output, ephemeral = True)
		else: await interaction.response.send_message(output, ephemeral = True)
		
	def display(self, e):
		return f"**{e}**: {self.names[e]}" if self.names else f"**{e}**"

class MessageModal(NvModal, title = "Set message"):
	message_text = ui.TextInput(
		label = "Message",
		placeholder = 
			"You can include GUILD_NAME, MENTION, or MEMBER_NAME. "
			"Leave blank to use the default.",
		style = discord.TextStyle.long
	)
	
	def __init__(self, leave, author, guild):
		super().__init__()
		
		self.author = author
		self.guild = guild
		self.leave = leave
		
		self.action_label = "leave" if self.leave else "welcome"
		self.title = f"Set {self.action_label} message"
	
	async def on_submit(self, interaction):
		message = self.message_text.value		
		message_type = "welcome_text" if not self.leave else "leave_text"
		
		if message == "": message = None
		
		await interaction.client.dbc.execute(
			f"UPDATE guilds SET {message_type} = ?1 WHERE discord_id = ?2;", 
			(message, self.guild.id)
		)
		
		await interaction.client.dbc.commit()
		await interaction.response.send_message(":white_check_mark: | Message changed.")
	
	async def interaction_check(self, interaction):
		return self.author == interaction.user

async def show(ctx, modal, button_text, message):
	if not ctx.interaction:
		confirm = ui.Button(label = button_text, style = discord.ButtonStyle.primary)
		confirm.callback = lambda i: i.response.send_modal(modal)
		
		view = views.NvView(timeout = 50)
		view.add_item(confirm)
		view.message = await ctx.send(message, view = view)
	else:		
		await ctx.interaction.response.send_modal(modal)
		
