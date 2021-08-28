
from jishaku.features.baseclass import Feature
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from .. import utils

FEATURES = (*OPTIONAL_FEATURES, *STANDARD_FEATURES)

for cmd in (c for f in FEATURES for c in f.__dict__.values()):
	if type(cmd) == Feature.Command and cmd.parent == "jsk": 
		#doesn't have any subclasses, so we are good
		cmd.parent = None
		
		if cmd.kwargs["name"] == "source":
			cmd.kwargs["name"] = "filesource"
		elif cmd.kwargs["name"] == "rtt":
			cmd.kwargs.pop("aliases")

class DebugTools(*FEATURES, utils.MeldedCog, name = "Debug", category = "Debug", limit = False):
	def __init__(self, bot):
		super().__init__(bot = bot)
		self.jsk.description = self.jsk.help = "Displays basic Jishaku info."
		
def setup(bot):
	bot.add_cog(DebugTools(bot))