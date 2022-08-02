from collections import namedtuple

__version__ = "5.0.0 beta"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021-2022 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified")
version_info = VersionInfo(major = 5, minor = 0, micro = 0, qualified = "beta")
