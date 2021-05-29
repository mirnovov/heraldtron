from collections import namedtuple

__version__ = "4.1.0"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified") 
version_info = VersionInfo(major = 4, minor = 1, micro = 0, qualified = "final")
