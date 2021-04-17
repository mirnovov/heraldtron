import re, os, setuptools

def getVersion():
	path = os.path.join(os.path.dirname(__file__),"ht","version.py")
	with open(path, "r", encoding="utf-8") as file:
		version = re.search("__version__ = ['\"]((\d|\w|\.)+)[\"']",file.read())
		
		if version: return version[1]
		else: return None

setuptools.setup(
	name = "heraldtron",
	version = getVersion(),
	author = "novov",
	author_email = "anon185441@gmail.com",
	packages = ["ht","ext"],
	package_data = {
		"ht": ["data/*"],
	},
	license = "MIT",
	python_requires = ">=3.7",
	install_requires = [
		"discord.py>=1.1.0",
		"python-dotenv>=0.17.0",
		"aiohttp>=3.7.4",
		"Pillow>=8.0"
	],
	extras_require = {
		"fast": ["cchardet>=2.1.7","aiodns>=2.0.0"]
	}
)