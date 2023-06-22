#!/usr/bin/env python

__author__ = "Baptiste Jouin (@baptistejouin)"
__copyright__ = "Copyright 2023, @baptistejouin"
__credits__ = ["Baptiste Jouin"]
__license__ = "MIT"
__version__ = "1.0"
__status__ = "Development"

import os, json
from notion_client import Client
from icalendar import Calendar, Event, vText
from datetime import datetime, timedelta

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
                        ][0]["plain_text"],
                        "date": object["properties"][config["DATE_PROPERTY"]]["date"],
                        "uid": object["id"],
                        "url": object["url"],
                        "created_time": object["created_time"],
                        "last_edited_time": object["last_edited_time"],
                        "description": "🫢 test de description",
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
            return datetime.strptime(date_str, fmt).date()
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

        current.add("summary", vText(event["title"]))
        current.add("dtstart", convert_to_datetime(event["date"]["start"]))
        if event["date"]["end"]:
            current.add("dtend", convert_to_datetime(event["date"]["end"]))
        current.add("created", convert_to_datetime(event["created_time"]))
        current.add("last-modified", convert_to_datetime(event["last_edited_time"]))
        current.add("description", f"{event['description']} \n {event['url']}")
        current.add("url", event["url"])
        current.add("sequence", 0)  # todo: increment sequence if needed
        # current.add("dtstamp", datetime.now())
        # current.add("location", vText(event["location"]))

        cal.add_component(current)


if __name__ == "__main__":
    notion = Client(auth=config["NOTION_TOKEN"])

    database_entries = getDatabaseEntries(notion)
    decoded_data = decode(database_entries)

    cal = Calendar()
    cal.add("prodid", f"-//{__author__}//cron-notion-ics//FR")
    cal.add("version", __version__)

    create_events(decoded_data, cal)

    with open(os.path.join(config["EXPORT_PATH"], "calendar.ics"), "wb") as f:
        f.write(cal.to_ical())
        print(f"Calendar exported to {config['EXPORT_PATH'] + '/calendar.ics'}")
        f.close()
