<img src="media/robot.png" width="250" alt="Heraldtron mascot">

# Heraldtron

A heraldry-related bot, designed for the [Heraldry Community](https://twitter.com/arm_yourselves).

## Requirements

* Python 3.9+
* [discord.py](https://pypi.org/project/discord.py/)
* [aiohttp](https://pypi.org/project/aiohttp/) (comes installed with discord.py)
* [Pillow](https://pypi.org/project/Pillow/)
* [aiosqlite](https://pypi.org/project/aiosqlite/)
* [docx2python](https://pypi.org/project/docx2python/)
* [python-dateutil](https://pypi.org/project/python-dateutil/)
* Developer credentials (see below)

[cchardet](https://pypi.org/project/cchardet/) and [aiodns](https://pypi.org/project/aiodns/) are also recommended to improve performance.

For convenience, these can all be installed with `pip install -r requirements/main.txt`. 

## Setup

As one may expect, this bot requires a *bot account* to run. Refer to the discord.py [instructions on creating one](https://discordpy.readthedocs.io/en/stable/discord.html) for more information. 

For some functionality, a [Google Cloud Platform](https://cloud.google.com) account is required, with the Custom Search and Google Drive APIs enabled. Custom search features additionally require a [Programmable Search](https://programmablesearchengine.google.com/about/) engine, since Google has discontinued general search APIs. This must have image search enabled, and it is strongly recommended that you enable the "Search the entire web" setting.

Before running, the bot requires an `config.json` file in the root directory containing data that it needs to run:

* `DISCORD_TOKEN`: The Discord Developer API token.
* `GCS_TOKEN`: The Google Cloud Platform API key. Custom Search and Google Drive must be enabled for this key.
* `GCS_CX`: The Programmable Search engine identifier.
* `AR_RIJKS`: The key for the [Rijksmuseum API](https://data.rijksmuseum.nl/object-metadata/api/).
* `AR_EURO`: The key for the [Europeana Pro API](https://pro.europeana.eu/page/apis).
* `AR_DGTNZ`: The key for the [Digital NZ API](https://digitalnz.org/developers).
* `AR_SMTHS`: The key for the [Smithsonian API](http://edan.si.edu/openaccess/apidocs/), provided by data.gov.
* `AR_DDBTK`: The key for the German Digital Library/[Deutsche Digitale Bibliothek API](https://labs.deutsche-digitale-bibliothek.de/app/ddbapi/)
* `DEEP_AI`: The key for `!textgen`, from [DeepAI](https://deepai.org/).

Additionally, there are a number of optional settings that can be specified:

* `USE_JISHAKU`: If `true`, load the [jishaku](https://github.com/Gorialis/jishaku) debugger (must be installed separately). 
* `OWNER_ONLY`: If `true`, disable usage of the bot for members that are not the owner. 
* `LOG_LEVEL`: The numeric [logging level](https://docs.python.org/3/library/logging.html#levels) for the bot. Defaults to 20 (`INFO`).
* `DB_PATH`: An alternate path for the SQLite file to use, instead of the default `data/db/heraldtron.db`.

## Usage

Once your bot is set up, use the standard Python package initialisation method (of course, use `python3` if there is an overlapping python2 install): 

```
cd path/to/heraldtron
python -m ht
```

Run the `!help` command for information about the bot's functionality.