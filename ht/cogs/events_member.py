import discord
from discord.ext import commands

class MemberEvents(commands.Cog, name = "Member events"):
	TIMEOUT_ROLE_ID = 1003513794909184001
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.register_timeouts())
		
	async def register_timeouts(self):
		await self.bot.wait_until_ready()
		if not self.bot.get_guild(self.bot.HERALDRY_GUILD): return

		self.timeout_role = self.bot.get_guild(self.bot.HERALDRY_GUILD).get_role(
			self.TIMEOUT_ROLE_ID
		)
		
		for member in self.timeout_role.members:
			if not member.is_timed_out():
				await member.remove_roles(self.timeout_role)
			else:
				self.bot.loop.create_task(self.will_remove_timeout(member))
		
	async def will_remove_timeout(self, member):
		await discord.utils.sleep_until(member.timed_out_until)
		await member.remove_roles(self.timeout_role)
	
	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if after.guild.id != self.bot.HERALDRY_GUILD: 
			return
		
		if after.is_timed_out() and not before.is_timed_out():
			await after.add_roles(self.timeout_role)
			await self.will_remove_timeout(after)
	
	@commands.Cog.listener()
	async def on_member_join(self, member):
		await self.post_welcome_message(member, False)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		await self.post_welcome_message(member, True)

	async def post_welcome_message(self, member, leave):
		guild_db = await self.bot.dbc.execute_fetchone("SELECT * FROM guilds WHERE discord_id == ?;", (member.guild.id,))

		if not guild_db or not guild_db["welcome_users"]:
			#if guild not in db (shouldn't happen) or if disabled
			return

		if leave: message, emoji = guild_db["leave_text"], ":outbox_tray:"
		else: message, emoji = guild_db["welcome_text"], ":inbox_tray:"

		if not message:
			message = f"We're sorry to see you leaving, **MEMBER_NAME**." if leave else f"Welcome to the **GUILD_NAME** server, MENTION."

		formatted = self.welcome_fmt(member, message)

		await member.guild.system_channel.send(f"{emoji} | {formatted}")

	def welcome_fmt(self, member, subst_text):
		if not subst_text: return None

		special_vars = {
			"GUILD_NAME": member.guild.name,
			"MEMBER_NAME": str(member),
			"MENTION": member.mention
		}

		for name, value in special_vars.items():
			subst_text = subst_text.replace(name,value)

		return subst_text

async def setup(bot):
	await bot.add_cog(MemberEvents(bot))
