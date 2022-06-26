import discord, typing, re
from discord.ext import commands
from datetime import datetime
from .. import embeds, utils, views

class ModerationTools(utils.ModCog, name = "Tools"):
	HAS_MARKDOWN = re.compile(r"<@!?|<#|<&|\*{1,2}\w")
	SHORT_MESSAGE = 200

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
	@commands.command(
		help = "Displays a moderator message in a channel.\n By default, this is"
		" the channel the command is invoked in, but it can be specified beforehand.",
		aliases = ("m",)
	)
	async def modmessage(self, ctx, *, message_content):
		if len(message_content) < self.SHORT_MESSAGE and not re.search(self.HAS_MARKDOWN, message_content):
			embed = embeds.MOD_MESSAGE.create(message_content, "")
		else:
			embed = embeds.MOD_MESSAGE.create("", message_content)

		embed.set_footer(
			text = f"Sent by {ctx.author.display_name} on {(datetime.now()).strftime('%d %B %Y')}",
			icon_url = ctx.author.display_avatar.with_size(256).url
		)

		await ctx.channel.send(embed = embed)
		
		if isinstance(ctx.channel, discord.Thread) and ctx.channel.archived:
			await ctx.channel.edit(locked = False, archived = False)
			await ctx.message.delete()
			await ctx.channel.edit(locked = True, archived = True)
		else:
			await ctx.message.delete()

	@commands.guild_only()
	@commands.command(help = "Locks a channel, disabling the ability to send messages from it.", aliases = ("l",))
	async def lock(self, ctx):
		await self.change_locking(ctx, ctx.channel, locked = True)

	@commands.guild_only()
	@commands.command(help = "Unlocks a channel, restoring the ability to send messages from it.", aliases = ("ul",))
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
			overwrite = discord.PermissionOverwrite(send_messages = not locked)
			await channel.set_permissions(ctx.guild.default_role, overwrite = overwrite)
			await ctx.send(f":{action_name}: | **{channel.mention} has been {action_name}ed.**")

def setup(bot):
	bot.add_cog(ModerationTools(bot))
