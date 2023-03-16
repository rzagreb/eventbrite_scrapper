import datetime
from typing import List

# from .context import eventbrite_scrapper
from eventbrite_scrapper import Eventbrite
from eventbrite_scrapper import data_models as dm

DT_TODAY = datetime.datetime.today().strftime("%Y-%m-%d")
DT_2W = (datetime.datetime.today() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")


def test_search():
    client = Eventbrite()
    search_params = {
        "region": "ca--san-francisco",
        "dt_start": DT_TODAY,
        "dt_end": DT_2W,
        "max_pages": 3,
    }

    events: List[dm.Event] = []
    for page_results in client.search_events.results_iter(**search_params):
        for e in page_results:
            events.append(e)

    must_have_cols = (
        "id",
        "hash",
        "name",
        "url",
        "is_online_event",
        "short_description",
        "published_datetime",
        "start_datetime",
        "end_datetime",
        "timezone",
        "hide_start_date",
        "hide_end_date",
        "tags_categories",
        "tags_formats",
        "primary_venue",
        "tickets_url",
        "image",
    )
    date_cols = (
        "published_datetime",
        "start_datetime",
        "end_datetime",
    )
    venue_cols = (
        "id",
        "name",
        "address",
        # "url",
    )
    venue_address_cols = (
        "city",
        "latitude",
        "longitude",
        "country",
        "region",
        "postal_code",
        "address_1",
        # "address_2",  # sometimes null
        "localized_area_display",
        "localized_address_display",
    )
    image_cols = (
        "id",
        "url",
    )

    for e in events:
        event_data = e.as_dict()
        for c in must_have_cols:
            assert event_data[c] is not None

        for c in date_cols:
            assert isinstance(event_data[c], datetime.datetime)

        for c in venue_cols:
            assert event_data["primary_venue"][c] is not None, [
                c,
                event_data["primary_venue"][c],
            ]

        for c in venue_address_cols:
            assert event_data["primary_venue"]["address"][c] is not None, [
                c,
                event_data["primary_venue"]["address"][c],
            ]

        for c in image_cols:
            assert event_data["image"][c] is not None


def test_profile():
    client = Eventbrite()

    # Get Event sample
    search_params = {
        "region": "ca--san-francisco",
        "dt_start": DT_TODAY,
        "dt_end": DT_2W,
        "max_pages": 2,
    }
    events = list(client.search_events.results_iter(**search_params))
    assert len(events)

    # Main
    event = events[0][0]
    event_profile = client.event_profile.load(event.url)

    must_have_cols = (
        "id",
        "name",
        "url",
        "is_online_event",
        "long_description",
        "short_description",
        "start_datetime",
        "end_datetime",
        "timezone",
        "is_cancelled",
        "hide_start_date",
        "hide_end_date",
        "primary_venue",
    )
    venue_cols = (
        "id",
        "name",
        # "full_address",
        "url",
    )
    event_data = event_profile.as_dict()
    for c in must_have_cols:
        assert event_data[c] is not None, ["must have", c, event_data.keys(), event.url]
    for c in venue_cols:
        assert event_data["primary_venue"][c] is not None, [
            "must have",
            c,
            event_data["primary_venue"].keys(),
            event.url,
        ]
