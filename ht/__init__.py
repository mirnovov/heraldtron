from collections import namedtuple

__version__ = "4.9.2"
__author__ = "novov"
__license__ = "MIT"
__copyright__ = "(c) 2021-2022 novov"

VersionInfo = namedtuple("VersionInfo", "major minor micro qualified")
version_info = VersionInfo(major = 4, minor = 9, micro = 2, qualified = "final")
