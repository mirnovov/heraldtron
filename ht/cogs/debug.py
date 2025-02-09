from jishaku.features.baseclass import Feature
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from .. import utils
from ..ext import AioSqliteConnectionAdapter

FEATURES = (*OPTIONAL_FEATURES, *STANDARD_FEATURES)

for cmd in (c for f in FEATURES for c in f.__dict__.values()):
	if type(cmd) == Feature.Command and cmd.parent == "jsk":
		#doesn't have any subclasses, so we are good
		cmd.parent = None

		if cmd.kwargs["name"] == "source":
			cmd.kwargs["name"] = "filesource"
		elif cmd.kwargs["name"] == "rtt":
			cmd.kwargs.pop("aliases")

class DebugTools(*FEATURES, utils.MeldedCog, name = "Debug", limit = False):
	def __init__(self, bot):
		super().__init__(bot = bot)
		
		self.jsk_hide.enabled = False
		self.jsk_show.enabled = False
		self.jsk.enabled = False
		
	def jsk_find_adapter(self, ctx): 
		return AioSqliteConnectionAdapter(ctx.bot.dbc), "bot.dbc"

async def setup(bot):
	await bot.add_cog(DebugTools(bot))
