from collections import namedtuple

__version__ = "4.0.3"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified") 
version_info = VersionInfo(major = 4, minor = 0, micro = 3, qualified = "final")
