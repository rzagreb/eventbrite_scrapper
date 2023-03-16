from typing import Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import copy
import datetime


@dataclass
class D:
    """Contains value that is used in the page params and to make API call"""

    api_id: str
    url_id: str


class Category:
    BUSINESS = D("EventbriteCategory/101", "business")
    FOOD_DRINK = D("EventbriteCategory/110", "food-and-drink")
    HEALTH = D("EventbriteCategory/107", "health")
    MUSIC = D("EventbriteCategory/103", "music")
    AUTO_BOAT_AIR = D("EventbriteCategory/118", "auto-boat-and-air")
    CHARITY_CAUSES = D("EventbriteCategory/111", "charity-and-causes")
    COMMUNITY = D("EventbriteCategory/113", "community")
    FAMILY_EDUCATION = D("EventbriteCategory/115", "family-and-education")
    FASHION = D("EventbriteCategory/106", "fashion")
    FILM_MEDIA = D("EventbriteCategory/104", "film-and-media")
    HOBBIES = D("EventbriteCategory/119", "hobbies")
    HOME_LIFESTYLE = D("EventbriteCategory/117", "home-and-lifestyle")
    PERFORMING_VISUAL_ARTS = D("EventbriteCategory/105", "arts")
    GOVERNMENT = D("EventbriteCategory/112", "government")
    SPIRITUALITY = D("EventbriteCategory/114", "spirituality")
    SCHOOL_ACTIVITIES = D("EventbriteCategory/120", "school-activities")
    SCIENCE_TECH = D("EventbriteCategory/102", "science-and-tech")
    HOLIDAY = D("EventbriteCategory/116", "holiday")
    SPORTS_FITNESS = D("EventbriteCategory/108", "sports-and-fitness")
    TRAVEL_OUTDOOR = D("EventbriteCategory/109", "travel-and-outdoor")
    OTHER = D("EventbriteCategory/199", "other")


class EventFormat:
    CLASS = D("EventbriteFormat/9", "classes")
    CONFERENCE = D("EventbriteFormat/1", "conferences")
    FESTIVAL = D("EventbriteFormat/5", "festivals")
    PARTY = D("EventbriteFormat/11", "parties")
    APPEARANCE = D("EventbriteFormat/19", "appearances")
    ATTRACTION = D("EventbriteFormat/17", "attractions")
    CONVENTION = D("EventbriteFormat/4", "conventions")
    EXPO = D("EventbriteFormat/3", "expos")
    GALA = D("EventbriteFormat/8", "galas")
    GAME = D("EventbriteFormat/14", "games")
    NETWORKING = D("EventbriteFormat/10", "networking")
    PERFORMANCE = D("EventbriteFormat/6", "performances")
    RACE = D("EventbriteFormat/15", "races")
    RALLY = D("EventbriteFormat/12", "rallies")
    RETREAT = D("EventbriteFormat/18", "retreats")
    SCREENING = D("EventbriteFormat/7", "screenings")
    SEMINAR = D("EventbriteFormat/2", "seminars")
    TOURNAMENT = D("EventbriteFormat/13", "tournaments")
    TOUR = D("EventbriteFormat/16", "tours")


@dataclass
class EventTag:
    id: str
    text: str

    # def as_list(self) -> Tuple[str]:
    #    return


@dataclass
class Address:
    city: str = field(default=None, repr=False)
    latitude: str = field(default=float, repr=False)
    longitude: str = field(default=float, repr=False)
    country: str = field(default=None, repr=False)
    region: str = field(default=None, repr=False)
    postal_code: str = field(default=None, repr=False)
    address_1: str = field(default=None, repr=False)
    address_2: str = field(default=None, repr=False)
    # address to display (combination of previous values)
    localized_area_display: str = field(default=None, repr=True)
    localized_address_display: str = field(default=None, repr=False)
    # available only on event profile
    full_address: str = field(default=None, repr=False)


@dataclass
class Venue:
    id: str = field(default=None, repr=False)
    name: str = field(default=None, repr=False)
    address: Address = field(default=Address, repr=False)
    description: str = field(default=None, repr=False)

    url: str = field(default=None, repr=False)
    twitter_handler: str = field(default=None, repr=False)
    facebook_handler: str = field(default=None, repr=False)
    organization_website: str = field(default=None, repr=False)


@dataclass
class Image:
    id: str = field(default=None, repr=False)
    url: str = field(default=None, repr=False)
    original_url: str = field(default=None, repr=False)


@dataclass
class Event:
    id: str = field(repr=True)
    hash: str = field(repr=False)
    name: str = field(repr=True)
    url: str = field(repr=False)
    is_online_event: bool = field(default=None, repr=False)
    long_description: Optional[str] = field(default=None, repr=False)
    short_description: Optional[str] = field(default=None, repr=False)

    published_datetime: Optional[datetime.datetime] = field(default=None, repr=False)
    start_datetime: Optional[datetime.datetime] = field(default=None, repr=False)
    end_datetime: Optional[datetime.datetime] = field(default=None, repr=False)
    timezone: str = field(default=None, repr=False)
    is_cancelled: None = field(default=None, repr=False)

    hide_start_date: bool = field(default=None, repr=False)
    hide_end_date: bool = field(default=None, repr=False)

    # Parent event and whether event series id
    parent_event_url: Optional[str] = field(default=None, repr=False)
    series_id: Union[str, None] = field(default=None, repr=False)

    primary_venue: Venue = field(default_factory=Venue, repr=False)

    tags_categories: Tuple[EventTag] = field(default_factory=tuple, repr=False)
    tags_formats: Tuple[EventTag] = field(default_factory=tuple, repr=False)
    tags_by_organizer: Tuple[EventTag] = field(default_factory=tuple, repr=False)

    tickets_url: str = field(default=None, repr=False)
    tickets_by: str = field(default=None, repr=False)
    checkout_flow: str = field(default=None, repr=False)

    language: str = field(default=None, repr=False)

    image: Image = field(default_factory=Image, repr=False)

    raw_search_data: Optional[dict] = field(default=None, repr=False)
    raw_profile_data: Optional[dict] = field(default=None, repr=False)

    def as_dict(self, flatten: bool = False) -> dict:
        output = {
            k: v
            for k, v in asdict(self).items()
            if k not in ("raw_search_data", "raw_profile_data")
        }

        if flatten:
            output = flatten_dict(output)
            output["raw_search_data"] = copy.deepcopy(self.raw_search_data)
            output["raw_profile_data"] = copy.deepcopy(self.raw_profile_data)
            return output

        output["raw_search_data"] = copy.deepcopy(self.raw_search_data)
        output["raw_profile_data"] = copy.deepcopy(self.raw_profile_data)
        return output


def flatten_dict(d: dict, sep: str = ".", pkey: str = "") -> dict:
    """
    It takes a dictionary, and returns a dictionary with all the keys flattened

    Args:
      d (Dict[str, Any]): dict - the dictionary to flatten
      sep (str): The separator to use between the keys. Defaults to `.`
      parent_key (str): The key of the parent dictionary.

    Returns:
      Dict[str, Any] A dictionary with the keys flattened.
    """
    items = []
    for k, v in d.items():
        new_key = f"{pkey}{sep}{k}" if pkey else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, sep, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)
