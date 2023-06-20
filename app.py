#!/usr/bin/env python

__author__ = "Baptiste Jouin (@baptistejouin)"
__copyright__ = "Copyright 2023, @baptistejouin"
__credits__ = ["Baptiste Jouin"]
__license__ = "MIT"
__version__ = "1.0"
__status__ = "Development"

import os, json
from notion_client import Client

"""
	Load config.json file
"""
with open("config.json", "r") as config_file:
    config = json.load(config_file)

"""
	Load Notion API
"""
notion = Client(auth=config["NOTION_TOKEN"])
