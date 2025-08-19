import discord, typing, re
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from .. import utils, views

class ModerationTools(utils.ModCog, name = "Tools"):
	SHORT_MESSAGE = 200
	HEADING = ":warning: Official moderator message"

	def __init__(self, bot):
		self.bot = bot
		self.locked_threads = set()
		
	@commands.Cog.listener()
	async def on_message(self, message):
		#to make thread locking work, the bot archives threads and redoes it each time a message is posted
		if message.channel.id not in self.locked_threads: 
			return
		
		#exempt unlock message
		elif any(message.content == f"{a}unlock" for a in await self.bot.get_prefix(message)):
			return
		
		await message.channel.edit(locked = True, archived = True)
	
	@commands.guild_only()	
	@commands.hybrid_command(
		help = "Displays a moderator message in a channel.\n",
		aliases = ("modmessage",)
	)
	@app_commands.describe(message = "The message to display.")
	async def m(self, ctx, *, message):
		if len(message) < self.SHORT_MESSAGE and not "\n" in message:
			view = views.Generic(message, "", heading = self.HEADING)
		else:
			view = views.Generic("", message, heading = self.HEADING)
			
		if not ctx.interaction:
			view.add_footer(
				f"Sent by {ctx.author.display_name} on {utils.stddate(datetime.now())}"
			)

			await ctx.send(view = view)
		
			if isinstance(ctx.channel, discord.Thread) and ctx.channel.archived:
				await ctx.channel.edit(locked = False, archived = False)
				await ctx.message.delete()
				await ctx.channel.edit(locked = True, archived = True)
			else:
				await ctx.message.delete()
		else:
			await ctx.send(view = view)

	@commands.guild_only()
	@commands.hybrid_command(help = "Locks a channel, disabling the ability to send messages from it.", aliases = ("l",))
	async def lock(self, ctx):
		await self.change_locking(ctx, ctx.channel, locked = True)

	@commands.guild_only()
	@commands.hybrid_command(help = "Unlocks a channel, restoring the ability to send messages from it.", aliases = ("ul",))
	async def unlock(self, ctx):
		await self.change_locking(ctx, ctx.channel, locked = False)
		
	async def change_locking(self, ctx, channel, locked):
		action_name = "unlock" if not locked else "lock"
		is_thread = isinstance(channel, discord.Thread)
		
		if is_thread and locked:
			await ctx.send(
				#before action so the bot posting doesn't unarchive it
				f":lock: | **{channel.mention} has been locked.** " 
			) 
						
			await channel.edit(locked = True, archived = True)
			self.locked_threads.add(channel.id)
		
		elif is_thread:
			await channel.edit(locked = False, archived = False)
			self.locked_threads.remove(channel.id)
			
			await ctx.send(f":unlock: | **{channel.mention} has been unlocked.**")	
					
		else:
			if ctx.guild.id == self.bot.HERALDRY_GUILD:
				overwrite = discord.PermissionOverwrite(send_messages = True)
				bot_role = ctx.guild.get_role(self.bot.HERALDRY_GUILD_ROLE)
				
				await channel.set_permissions(bot_role, overwrite = overwrite)		
			
			overwrite = discord.PermissionOverwrite(send_messages = not locked)
			await channel.set_permissions(ctx.guild.default_role, overwrite = overwrite)
			await ctx.send(f":{action_name}: | **{channel.mention} has been {action_name}ed.**")

async def setup(bot):
	await bot.add_cog(ModerationTools(bot))
