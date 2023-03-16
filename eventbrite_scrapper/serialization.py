import logging
from typing import Dict, Any
import datetime

from . import data_models as dm

import pytz

log = logging.getLogger("eventbrite.serialization")


def serialize_event_search_result(data: Dict[str, Any]) -> dm.Event:
    _id = data.get("id")
    if not _id:
        _id = data.get("eventbrite_event_id")
    if not _id:
        _id = data["eid"]

    tz = pytz.timezone(data["timezone"])

    start_dt = norm_event_datetime(data["start_date"], data["start_time"], tz)
    end_dt = norm_event_datetime(data["end_date"], data["end_time"], tz)

    published_dt = datetime.datetime.strptime(
        data.get("published"), "%Y-%m-%dT%H:%M:%SZ"
    )
    published_dt = published_dt.replace(tzinfo=pytz.utc)

    tags_categories = []
    tags_formats = []
    tags_by_organizer = []
    for i in data.get("tags", []):
        i: dict
        tag = dm.EventTag(id=i["tag"], text=i["display_name"])
        if i.get("prefix", "") == "EventbriteCategory":
            tags_categories.append(tag)
        elif i.get("prefix", "") == "EventbriteFormat":
            tags_formats.append(tag)
        elif i.get("_type", "") == "tag":
            tags_by_organizer.append(tag)

    venue = data.get("primary_venue", {})

    event = dm.Event(
        id=_id,
        hash=data["dedup"]["hash"],
        name=data["name"],
        url=data["url"],
        parent_event_url=data.get("parent_url"),
        is_online_event=data["is_online_event"],
        long_description=data["full_description"],  # null
        short_description=data["summary"],
        # dates
        start_datetime=start_dt,
        end_datetime=end_dt,
        published_datetime=published_dt,
        timezone=data["timezone"],
        hide_start_date=data.get("hide_start_date"),
        hide_end_date=data.get("hide_end_date"),
        is_cancelled=data.get("is_cancelled"),
        # other
        tags_categories=tuple(tags_categories),
        tags_formats=tuple(tags_formats),
        tags_by_organizer=tuple(tags_by_organizer),
        primary_venue=dm.Venue(
            id=venue.get("id"),
            name=venue.get("name"),
            address=dm.Address(
                city=venue.get("address", {}).get("city"),
                # coordinates
                latitude=float(venue.get("address", {}).get("latitude")),
                longitude=float(venue.get("address", {}).get("longitude")),
                # address parts
                country=venue.get("address", {}).get("country"),
                region=venue.get("address", {}).get("region"),
                postal_code=venue.get("address", {}).get("postal_code"),
                address_1=venue.get("address", {}).get("address_1"),
                address_2=venue.get("address", {}).get("address_2"),
                # address display
                localized_area_display=venue.get("address", {}).get(
                    "localized_area_display"
                ),
                localized_address_display=venue.get("address", {}).get(
                    "localized_address_display"
                ),
            ),
            url=None,
        ),
        image=dm.Image(
            id=data.get("image", {}).get("id"),
            url=data.get("image", {}).get("url"),
            original_url=data.get("image", {}).get("original", {}).get("url"),
        ),
        tickets_url=data.get("tickets_url"),
        tickets_by=data.get("tickets_by"),
        checkout_flow=data.get("checkout_flow"),
        series_id=data.get("series_id"),
        language=data.get("language"),
        # debug
        raw_search_data=data,
    )

    return event


def serialize_event_profile(data: Dict[str, Any]) -> dm.Event:
    # shortcuts
    d_event: dict = data["event"]
    organizer: dict = data["organizer"]

    comp: dict = data["components"]
    event_desc: dict = comp["eventDescription"]
    event_map: dict = comp["eventMap"]

    # main
    start_datetime = datetime.datetime.strptime(
        d_event.get("start", {}).get("utc"), "%Y-%m-%dT%H:%M:%SZ"
    )
    start_datetime = start_datetime.replace(tzinfo=pytz.utc)

    end_datetime = datetime.datetime.strptime(
        d_event.get("end", {}).get("utc"), "%Y-%m-%dT%H:%M:%SZ"
    )
    end_datetime = end_datetime.replace(tzinfo=pytz.utc)

    # components.eventDescription.structuredContent.modules
    long_description = ""
    for i in event_desc.get("structuredContent", {}).get("modules", []):
        if i.get("type") == "text":
            long_description += f'<div>{i["text"]}</div>\n'
        elif i.get("type") == "image":
            long_description += f'<img href="{i["url"]}">\n'
        else:
            log.warning(f"Unknown content type: {i}")

    event = dm.Event(
        id=d_event["id"],
        hash=None,
        name=d_event["name"],
        url=d_event["url"],
        parent_event_url=None,
        is_online_event=d_event["isOnlineEvent"],
        long_description=long_description,
        short_description=event_desc["summary"],
        # dates
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        published_datetime=None,  # not included
        timezone=d_event.get("end", {}).get("timezone"),  # not included
        hide_start_date=d_event.get("hideStartDate"),
        hide_end_date=d_event.get("hideEndDate"),
        is_cancelled=(
            d_event.get("compactCheckoutDisqualifications", {}).get("is_canceled")
        ),
        # other
        tags_categories=None,  # different format
        tags_formats=None,  # different format
        tags_by_organizer=None,  # different format
        primary_venue=dm.Venue(
            id=organizer["id"],
            name=organizer["name"],
            description=organizer["description"],
            address=dm.Address(
                city=None,  # not included
                latitude=None,  # not included
                longitude=None,  # not included
                # address parts
                country=None,  # not included
                region=None,  # not included
                postal_code=None,  # not included
                address_1=None,  # not included
                address_2=None,  # not included
                # address display
                localized_area_display=None,  # not included
                localized_address_display=None,  # not included
                full_address=event_map.get("venueAddress"),
            ),
            url=organizer["url"],
            twitter_handler=organizer.get("orgTwitter"),
            facebook_handler=organizer.get("orgFacebook"),
            organization_website=organizer.get("orgWebsite"),
        ),
        image=dm.Image(
            id=None,  # too complex - unreliable
            url=None,  # too complex - unreliable
            original_url=None,  # too complex - unreliable
        ),
        tickets_url=None,  # not included
        tickets_by=None,  # not included
        checkout_flow=None,  # not included
        series_id=None,  # not included - only whether exists
        language=None,  # not included
        # debug
        raw_search_data=None,  # not relevant
        raw_profile_data=data,
    )

    return event


def norm_event_datetime(
    date_str: str,
    time_str: str,
    tz: pytz.BaseTzInfo,
) -> datetime.datetime:
    dt_str = f"{date_str} {time_str}"
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

    dt = tz.localize(dt)
    dt = dt.astimezone(pytz.utc)

    return dt
