from collections import namedtuple

__version__ = "4.6.1"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021-2022 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified") 
version_info = VersionInfo(major = 4, minor = 6, micro = 1, qualified = "final")
