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


async def getDatabaseMetadata(notion: Client):
    """
    Get the database metadata

    @type notion: Client
    @param notion: Notion client

    @rtype: dict
    @return: Database metadata
    """
    return await notion.databases.retrieve(
        **{
            "database_id": config["DATABASE_ID"],
        }
    )


def getDatabaseEntries(notion: Client):
    """
    Get all the database entries

    @type notion: Client
    @param notion: Notion client

    @rtype: list
    @return: Database entries
    """
    databaseEntries = []
    query = {"has_more": True, "next_cursor": None}
    while query["has_more"]:
        query = notion.databases.query(
            **{
                "database_id": config["DATABASE_ID"],
                "page_size": 100,
                "start_cursor": query["next_cursor"],
                "filter": config["FILTER"],
            }
        )
        databaseEntries.append(query["results"])
        # flatten the list
        databaseEntries = [item for sublist in databaseEntries for item in sublist]
    return databaseEntries


def decode(databaseEntries):
    """
    Decode the database entries to get only the title and the date

    @type databaseEntries: list
    @param databaseEntries: Database entries

    @rtype: list
    @return: Decoded database entries
    """
    filtered = []
    for object in databaseEntries:
        if object["properties"][config["DATE_PROPERTY"]]["date"] is not None:
            filtered.append(
                [
                    {
                        "title": object["properties"][config["TITLE_PROPERTY"]][
                            "title"
                        ][0]["text"]["content"],
                        "date": object["properties"][config["DATE_PROPERTY"]]["date"],
                    }
                ]
            )
        else:
            print(
                f"Date property named {config['DATE_PROPERTY']} is empty for this Database, verify your config.json file."
            )
            exit()
    return filtered


if __name__ == "__main__":
    notion = Client(auth=config["NOTION_TOKEN"])

    database_entries = getDatabaseEntries(notion)
    decoded_data = decode(database_entries)

    print(decoded_data)
