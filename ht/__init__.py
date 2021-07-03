from collections import namedtuple

__version__ = "4.3.4"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified") 
version_info = VersionInfo(major = 4, minor = 3, micro = 3, qualified = "final")
