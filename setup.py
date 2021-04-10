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
	packages = ["ht"],
	license = "MIT",
	python_requires = ">=3.6",
	install_requires = [
		"discord.py>=1.1.0",
		"python_dotenv"
	]
)