#!/usr/bin/env python

__author__ = "Baptiste Jouin (@baptistejouin)"
__copyright__ = "Copyright 2023, @baptistejouin"
__credits__ = ["Baptiste Jouin"]
__license__ = "MIT"
__version__ = "1.0"
__status__ = "Production"

import os, json
from notion_client import Client
from icalendar import Calendar, Event
from datetime import datetime, timedelta, timezone

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


def getFirstContentBlock(notion: Client, block_id: str):
    """
    Get the content of a block

    @type notion: Client
    @param notion: Notion client

    @type block_id: str
    @param block_id: Block ID

    @rtype: str
    @return: Block content
    """
    block = notion.blocks.children.list(
        **{
            "block_id": block_id,
            "page_size": config["MAX_BLOCK_PAGE_SIZE"],
        }
    )

    # For each type of block, get the content, and build a string
    plain_text = ""

    numbered_item_count = 1  # Counter for numbered list items

    for obj in block["results"]:
        obj_type = obj["type"]
        try:
            rich_text = obj[obj_type]["rich_text"][0]

            if rich_text.get("href"):
                plain_text += rich_text["href"]
            elif rich_text.get("plain_text"):
                if obj_type.startswith("heading"):
                    heading_level = obj_type.split("_")[
                        1
                    ]  # Extract the heading level number
                    heading_symbols = "#" * int(heading_level)
                    plain_text += heading_symbols + " " + rich_text["plain_text"]
                elif obj_type == "bulleted_list_item":
                    plain_text += "• " + rich_text["plain_text"]
                elif obj_type == "numbered_list_item":
                    plain_text += f"{numbered_item_count}. " + rich_text["plain_text"]
                    numbered_item_count += 1
                else:
                    plain_text += rich_text["plain_text"]
            plain_text += "\n"  # Add a line break after each block
        except (KeyError, IndexError):
            continue

    return plain_text


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
                        ][0]["plain_text"],
                        "emoji": f'{object["icon"]["emoji"]} '
                        if (
                            (object["icon"] is not None)
                            and (object["icon"]["type"] == "emoji")
                        )
                        else "",
                        "date": object["properties"][config["DATE_PROPERTY"]]["date"],
                        "uid": object["id"],
                        "url": object["url"],
                        "created_time": object["created_time"],
                        "last_edited_time": object["last_edited_time"],
                        "description": getFirstContentBlock(notion, object["id"]),
                    }
                ]
            )
        else:
            print(
                f"Date property named {config['DATE_PROPERTY']} is empty for this Database, verify your config.json file."
            )
            exit()
    # flatten the list
    filtered = [item for sublist in filtered for item in sublist]
    return filtered


def convert_to_datetime(date_str):
    """
    Convert a date string from Notion API to datetime

    @type date_str: str
    @param date_str: Date string

    @rtype: datetime
    @return: Datetime
    """
    formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f%z"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    raise ValueError("Invalid date format: " + date_str)


def create_events(decoded_data, cal):
    """
    Create an event

    @type decoded_data: list
    @param decoded_data: Decoded database entries

    @type cal: Calendar
    @param cal: Calendar

    @rtype: void
    @return: void

    """
    for event in decoded_data:
        current = Event()

        current.add("uid", event["uid"])
        current.add("summary", f"{event['emoji']}{event['title']}")
        current.add("dtstamp", datetime.now())
        current.add("created", convert_to_datetime(event["created_time"]))
        current.add("last-modified", convert_to_datetime(event["last_edited_time"]))
        current.add("description", event["description"])
        current.add("url", event["url"])
        current.add("sequence", 0)  # default value
        current.add("transp", "OPAQUE")  # default value
        current.add("status", "CONFIRMED")  # default value

        if event["date"]["end"]:
            dt_start = convert_to_datetime(event["date"]["start"])
            dt_end = convert_to_datetime(event["date"]["end"])
            current.add("dtstart", dt_start.astimezone(timezone.utc))
            current.add("dtend", dt_end.astimezone(timezone.utc))
        else:
            dt_start = convert_to_datetime(event["date"]["start"]).date()
            current.add("dtstart", dt_start)
            current.add("dtend", dt_start + timedelta(days=1))

        cal.add_component(current)


if __name__ == "__main__":
    notion = Client(auth=config["NOTION_TOKEN"])

    database_entries = getDatabaseEntries(notion)
    decoded_data = decode(database_entries)

    cal = Calendar()
    cal.add("prodid", f"-//{__version__}//cron-notion-ics//FR")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", "Notion Sync")
    cal.add("X-WR-TIMEZONE", "UTC")
    cal.add("CALSCALE", "GREGORIAN")
    cal.add("METHOD", "PUBLISH")

    create_events(decoded_data, cal)

    with open(os.path.join(config["EXPORT_PATH"], "calendar.ics"), "wb") as f:
        f.write(cal.to_ical())
        print(f"Calendar exported to {config['EXPORT_PATH'] + '/calendar.ics'}")
        f.close()
