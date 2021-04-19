<img src="images/robot.png" width="250" alt="Heraldtron mascot">

# Heraldtron

A heraldry-related bot, designed for the [Heraldry Community](https://twitter.com/arm_yourselves). Still very much a work in progress.

## Requirements

* Python 3.7+
* [discord.py](https://pypi.org/project/discord.py/)
* [aiohttp](https://pypi.org/project/aiohttp/) (comes installed with discord.py)
* [Pillow](https://pypi.org/project/Pillow/)
* Developer credentials (see below)

[cchardet](https://pypi.org/project/cchardet/) and [aiodns](https://pypi.org/project/aiodns/) are also recommended to improve performance. 

## Setup

As one may expect, this bot requires a *bot account* to run. Create one in the Discord Developer Portal ([see here for a basic how to](https://realpython.com/how-to-make-a-discord-bot-python/)). 

For image search functionality, a [Google Cloud Platform](https://cloud.google.com) account, with the Custom Search API enabled, is required. You must also create a [Programmable Search](https://programmablesearchengine.google.com/about/) engine that Custom Search uses, since Google has discontinued general search APIs. This must have image search enabled, and it is strongly recommended that you enable the "Search the entire web" setting.

Before running, the bot requires an `config.json` file in the root directory containing credentials that it needs to run:

* `DISCORD_TOKEN`: The Discord Developer API token.
* `GCS_TOKEN`: The Google Cloud Platform API key. Custom Search must be enabled for this key.
* `GCS_CX`: The Programmable Search engine identifier.
* `MAINTAINER`: The internal Discord user integer (*not* the tag plus 4-digit unique number) that is messaged when errors occur.

Additionally, the `!artifact` command requires a number of museum and institutional API keys, which are specified below:

* `AR_RIJKS`: The key for the [Rijksmuseum API](https://data.rijksmuseum.nl/object-metadata/api/).
* `AR_EURO`: The key for the [Europeana Pro API](https://pro.europeana.eu/page/apis).
* `AR_DGTNZ`: The key for the [Digital NZ API](https://digitalnz.org/developers).
* `AR_SMTHS`: The key for the [Smithsonian API](http://edan.si.edu/openaccess/apidocs/), provided by data.gov.
* `AR_DDBTK`: The key for the German Digital Library/[Deutsche Digitale Bibliothek API](https://labs.deutsche-digitale-bibliothek.de/app/ddbapi/)

A few other services require keys as well:

* `DEEP_AI`: The key for `!textgen`, from [DeepAI](https://deepai.org/).

## Usage

Once your bot is set up, use the standard Python package initialisation method (of course, use `python3` if there is an overlapping python2 install): 

```
cd path/to/heraldtron
python -m ht
```

Run the `!help` command for information about the bot's functionality.