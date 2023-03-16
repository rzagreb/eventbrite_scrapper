# Eventbrite Scrapper

This Python module provides a simple interface for scraping data from the Eventbrite website. This module lets you easily extract search results and parse individual event pages.

**Disclaimer:** This module is **only intended for educational use**. Please use this module responsibly and do not abuse it. We do not endorse or condone any unauthorized or illegal use of this module, including but not limited to using it to scrape data from Eventbrite for commercial purposes or using it to violate Eventbrite's terms of service. By using this module, you assume full responsibility for your actions and agree to use it in compliance with all applicable laws and regulations. The authors of this module are not responsible for any misuse or abuse of this module.

## Installation

To install the Eventbrite Scrapper module, you can use pip:

```bash
pip install git+https://github.com/rzagreb/eventbrite_scrapper.git
```

## Usage

### Search

Here's a simple example of how to use the module to search events:

```python
from eventbrite_scrapper import Eventbrite

client = Eventbrite()

events = client.search_events.get_results(
    region="ca--san-francisco",  # can be found in URL through browser
    dt_start="2023-03-20", # start date range to search events
    dt_end="2023-03-25",  # end date range to search events
    max_pages=2,  # number of pages to check
)
event = events[0]

print(event.id)  # (str) unique eventbrite event identificator
print(event.name)  # (str) event name
print(event.url)  # (str) url to event page
print(event.is_online_event)  # (bool) True this is online event
print(event.short_description)  # (str)
print(event.published_datetime)  # (datetime) when event was created, in utc
print(event.start_datetime)  # (datetime) time event starts, in utc
print(event.end_datetime)  # (datetime) time event ends, in utc
print(event.timezone)  # (str)
print(event.hide_start_date)  # (str) True if time not displayed to user
print(event.hide_end_date)  # (str) True if time not displayed to user
print(event.parent_event_url)  # (str) URL of the parent event
print(event.series_id)  # (str) identificator of the series of events
print(event.primary_venue.id)  # (str) Organizer id
print(event.primary_venue.name)  # (str) Organizer name
print(event.primary_venue.url)  # (str) URL to organizer page
print(event.primary_venue.address.latitude)  # (float)
print(event.primary_venue.address.longitude)  # (float)
print(event.primary_venue.address.region)  # (str)
print(event.primary_venue.address.postal_code)  # (str)
print(event.primary_venue.address.address_1)  # (str)
print(event.tickets_url)  # (str) url to buy tickets
print(event.checkout_flow)  # (str)
print(event.language)  # (str)
print(event.image.url)  # (str) URL for image for the event
print(event.tags_categories[0].text)  # (str) Eventbrite category
print(event.tags_formats[0].text)  # (str) Eventbrite event format
print([tag.text for tag in event.tags_by_organizer])  # (list[str]) Organizer's tags
```

In this example, we extract events for San Francisco, then we print out event attributes

You can also specify additional parameters when scraping events. For example, you can use the `category` parameter to filter events by category, or the `sort_by` parameter to sort events by date, relevance, or popularity:

```python
from eventbrite_scrapper.data_models import Category, EventFormat

events = client.search_events.get_results(
    region="ca--san-francisco",  # can be found in URL through browser
    dt_start="2023-03-20", 
    dt_end="2023-03-25",
    category=Category.MUSIC,  # must use constant
    event_format=EventFormat.FESTIVAL,  # must use constant
  	price='free',  # could be also `paid`
    max_pages=2,
)
```

For more information about the available parameters, see the module documentation.

### Event Page

Here's a simple example of how to parse events pages:

```python
from eventbrite_scrapper import Eventbrite

client = Eventbrite()

url = "https://www.eventbrite.com/e/some-event-path-555555555555"
event = client.event_profile.load(url)

print(event.id)
print(event.name)
print(event.url)
print(event.long_description)  # (str) html content
print(event.short_description)
print(event.start_datetime)
print(event.end_datetime)
print(event.timezone)
print(event.primary_venue.id)  # (str) Organizer id
print(event.primary_venue.name)  # (str) Organizer name
print(event.primary_venue.url)  # (str) URL to organizer page
print(event.primary_venue.twitter_handler)  # (str)
print(event.primary_venue.facebook_handler)  # (str)

```

In this example, we parse event page `url`, then output available values.

## Advanced usage

### Client parameters 

```python
import requests
from eventbrite_scrapper import Eventbrite

my_session = requests.Session()
headers = {
    "User-Agent": 'My User agent',
}

client = Eventbrite(session= my_session, headers)

# Overwritting default delay between request (to avoid ban)
# In this example, it will be randomly set between 0.2 and 1 sec,
# but it could also take constant numbers
client.delay_between_fetches = (0.2, 1)
```
### Search Iterator

You can use page search iterator to search one page at a time.

```python
params = {
    "region": "ca--san-francisco",
    "dt_start": "2023-03-20",
    "dt_end": "2023-03-25",
    "max_pages": 2,
}
for page_results in client.search_events.results_iter(**params):
    for event in page_results:
        pass
```

### Exports

In order to get event as dictionary you need to call `.as_dict()` method.

```python
event.as_dict()
```

There is also option to flatten the hierarchy of the event attributes

```python
event.as_dict(flatten=True)
```

### List of Categories 

Here is list of categories that could be used in search parameters

```python
CATEGORY.BUSINESS
CATEGORY.FOOD_DRINK
CATEGORY.HEALTH
CATEGORY.MUSIC
CATEGORY.AUTO_BOAT_AIR
CATEGORY.CHARITY_CAUSES
CATEGORY.COMMUNITY
CATEGORY.FAMILY_EDUCATION
CATEGORY.FASHION
CATEGORY.FILM_MEDIA
CATEGORY.HOBBIES
CATEGORY.HOME_LIFESTYLE
CATEGORY.PERFORMING_VISUAL_ARTS
CATEGORY.GOVERNMENT
CATEGORY.SPIRITUALITY
CATEGORY.SCHOOL_ACTIVITIES
CATEGORY.SCIENCE_TECH
CATEGORY.HOLIDAY
CATEGORY.SPORTS_FITNESS
CATEGORY.TRAVEL_OUTDOOR
CATEGORY.OTHER
```

### List of EventFormat 

Here is list of event format that could be used in search parameters.

```python
EventFormat.CLASS
EventFormat.CONFERENCE
EventFormat.FESTIVAL
EventFormat.PARTY
EventFormat.APPEARANCE
EventFormat.ATTRACTION
EventFormat.CONVENTION
EventFormat.EXPO
EventFormat.GALA
EventFormat.GAME
EventFormat.NETWORKING
EventFormat.PERFORMANCE
EventFormat.RACE
EventFormat.RALLY
EventFormat.RETREAT
EventFormat.SCREENING
EventFormat.SEMINAR
EventFormat.TOURNAMENT
EventFormat.TOUR
```

## Testing

The Eventbrite Scrapper module comes with a suite of tests to ensure that it works as expected. You can find the tests in the `tests` directory of the module.

To run the tests using `pytest`, you first need to install the `pytest` package:

```bash
pip install pytest
```

Once `pytest` is installed, you can simply run the following command from the root directory of the module:

```bash
pytest
```

This will automatically discover and run all the tests in the `tests` directory. You should see a summary of the test results, along with any failures or errors that occurred.


## License

This module is released under the MIT license. See the LICENSE file for more information.

## Contributing

If you find any bugs or issues with this module, please submit an issue on the GitHub repository. If you would like to contribute to the module, feel free to submit a pull request with your changes.