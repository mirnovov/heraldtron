from collections import namedtuple

__version__ = "4.0.0rc1"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified") 
version_info = VersionInfo(major = 0, minor = 1, micro = 0, qualified = "rc1")
