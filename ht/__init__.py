from collections import namedtuple

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified")
version_info = VersionInfo(major = 4, minor = 14, micro = 0, qualified = "final")

__version__ = (
	f"{version_info.major}."
	f"{version_info.minor}."
	f"{version_info.micro}"
	f" {'' if version_info.qualified == 'final' else version_info.qualified}"
)
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021-2023 novov"

