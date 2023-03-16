from typing import Iterator, Union, List, Dict, Literal
import json
import re
import logging
import datetime
from urllib.parse import quote as url_encode

from . import data_models as dm
from . import utils
from .serialization import serialize_event_search_result, serialize_event_profile

import requests
import lxml.html

log = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Host": "www.eventbrite.com",
    "Origin": "https://www.eventbrite.com",
    "Pragma": "no-cache",
    "sec-ch-ua": (
        '".Not/A)Brand";v="99", "Google Chrome"; v="103", "Chromium";v="103"'
    ),
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/102.0.0.0 Safari/537.36"
    ),
}


class Eventbrite:
    """Uses combination of web scrapping and unoffical API to obtain data from
    eventbrite.com
    """

    def __init__(
        self,
        session: requests.Session = None,
        headers: Dict[str, str] = None,
    ):
        self.session = session if session else requests.Session()
        self.headers = headers if headers else DEFAULT_HEADERS

        self.waiter = utils.WaitManager()
        self.delay_between_fetches = (0.2, 1)

    @property
    def search_events(self) -> "EventSearch":
        return EventSearch(self)

    @property
    def event_profile(self) -> "EventProfile":
        return EventProfile(self)


class EventSearch:
    def __init__(self, parent: "Eventbrite"):
        self.p = parent

    def results_iter(
        self,
        region: str,
        dt_start: Union[str, datetime.datetime],
        dt_end: Union[str, datetime.datetime],
        price: Literal["paid", "free"] = None,
        category: dm.Category = None,
        event_format: dm.EventFormat = None,
        max_pages: int = 10,
    ) -> Iterator[List[dm.Event]]:
        """This function iterates through the pages of the search results, and yields
           page results

        Args:
          region (str): str
          dt_start (Union[str, datetime.datetime]): The start date of the search.
          dt_end (Union[str, datetime.datetime]): The end date of the search.
          price (Literal["paid", "free"]): event price. Defaults to None (all events)
          category (CATEGORY): event category
          event_format (EVENT_FORMAT): event format
          max_pages (int): The maximum number of pages to iterate. Defaults to 10 pages
            Note that iterator will stop when search reached it's end

        Yields:
            List[Event] - single page events results
        """
        # NOTE: results are fetched differently for the 1st page and 2nd+
        self.p.waiter.wait_if_needed(self.p.delay_between_fetches)
        log_page_num = "search {}/{}"

        # Page 1: Fetch
        # (contains results in html code)
        log.info(log_page_num.format(1, max_pages))
        page1_url = URL.search_page(
            region=region,
            dt_start=dt_start,
            dt_end=dt_end,
            price=price,
            category=category,
            event_format=event_format,
        )
        page1_content = self.__fetch_search_page(url=page1_url)

        # Page 1: Parse
        page1_data = self.__parse_search_page(page1_content)
        csrf_token = page1_data["csrf_token"]
        place_id = page1_data["results"]["placeId"]
        results = page1_data["results"]["search_data"]["events"]["results"]
        if not results:
            return
        events = [serialize_event_search_result(i) for i in results]
        yield events

        if max_pages == 1:
            return

        # Page 2: Fetch & Parse
        # (pulls search results from unofficial API)
        timezone = events[0].timezone
        for page_n in range(1, max_pages):
            log.info(log_page_num.format(page_n + 1, max_pages))
            self.p.waiter.wait_if_needed(self.p.delay_between_fetches)

            data = self.__fetch_search_api(
                places=[place_id],
                dt_start=dt_start,
                dt_end=dt_end,
                price=price,
                category=category,
                event_format=event_format,
                client_timezone=timezone,
                # additional requirements
                referer_url=page1_url,
                csrf_token=csrf_token,
                page_n=page_n + 1,
            )

            results = data["events"]["results"]
            if not results:
                return

            events = [serialize_event_search_result(i) for i in results]
            yield events

            log.debug(f"waiting for {self.p.delay_between_fetches} sec")

    def get_results(
        self,
        region: str,
        dt_start: Union[str, datetime.datetime],
        dt_end: Union[str, datetime.datetime],
        price: Literal["paid", "free"] = None,
        category: dm.Category = None,
        event_format: dm.EventFormat = None,
        max_pages: int = 10,
    ) -> List[dm.Event]:
        output = []

        for page_results in self.results_iter(
            region=region,
            dt_start=dt_start,
            dt_end=dt_end,
            price=price,
            category=category,
            event_format=event_format,
            max_pages=max_pages,
        ):
            for event in page_results:
                output.append(event)
        return output

    def __fetch_search_page(self, url: str) -> str:
        """Fetch content from HTML page"""
        headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;"
                "q=0.8,application/signed-exchange;"
                "v=b3;q=0.9"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "www.eventbrite.com",
            "Pragma": "no-cache",
            "sec-ch-ua": self.p.headers["sec-ch-ua"],
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": self.p.headers["sec-ch-ua-platform"],
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.p.headers["User-Agent"],
        }

        r = self.p.session.get(url, headers=headers)
        data = r.content.decode("utf-8")

        return data

    def __parse_search_page(self, content: str) -> dict:
        """
        It takes the HTML of a search page, parses it, and returns a dictionary with
        the CSRF token and the JSON with the search results.

        Args:
          content (str): the HTML content of the search page

        Returns:
          A dictionary with two keys:
            - csrf_token
            - results
        """
        tree = lxml.html.fromstring(content)

        # SEARCH RESULTS:
        # getting JSON with search results in <script>...</script>
        raw_results = re.findall(
            r"(?ims)window\.\_\_SERVER_DATA\_\_ \=(.*?\})\;",
            tree.xpath("//script[contains(.,'window.__SERVER_DATA__')]")[0].text,
        )
        results = json.loads(raw_results[0].strip())

        data = {
            "csrf_token": self.__extract_csrf_token(tree),
            "results": results,
        }
        return data

    @staticmethod
    def __extract_csrf_token(value: Union[str, lxml.html.HtmlElement]) -> str:
        """
        It takes a string or an lxml.html.HtmlElement object, and returns csrf token

        Args:
          value (Union[str, Any]): The HTML string or lxml.html.HtmlElement object to
            extract the CSRF
        token from.

        Returns:
          The csrf token is being returned.
        """
        if isinstance(value, str):
            tree = lxml.html.fromstring(value)
        else:
            tree = value

        xpath = "//input[@name='csrfmiddlewaretoken']"
        csrf_token = tree.xpath(xpath)[0].get("value")

        return csrf_token

    def __fetch_search_api(
        self,
        referer_url: str,
        csrf_token: str,
        places: List[str],
        page_n: int,
        dt_start: str,
        dt_end: str,
        client_timezone: str,
        category: dm.D = None,
        event_format: dm.D = None,
        online_events_only: bool = False,
        price: Literal["paid", "free"] = None,
    ) -> dict:
        if page_n < 2:
            raise NotImplementedError("Page for api must be at least 2")

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "DNT": "1",
            "Host": "www.eventbrite.com",
            "Origin": "https://www.eventbrite.com",
            "Pragma": "no-cache",
            "Referer": referer_url,
            "sec-ch-ua": self.p.headers["sec-ch-ua"],
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": self.p.headers["sec-ch-ua-platform"],
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.p.headers["User-Agent"],
            "X-CSRFToken": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
        }

        url = URL.search_page_api()
        data = {
            "event_search": {
                "date_range": {
                    "from": dt_start,
                    "to": dt_end,
                },
                "dates": "current_future",
                "dedup": True,
                "places": [str(i) for i in places],  # e.g ["85921881"]
                "page": page_n,
                "page_size": 20,
                "online_events_only": online_events_only,
                "client_timezone": client_timezone,
                "include_promoted_events_for": {
                    "interface": "search",
                    "request_source": "web",
                },
                # price (added later)
            },
            "expand.destination_event": [
                "primary_venue",
                "image",
                "ticket_availability",
                "saves",
                "event_sales_status",
                "primary_organizer",
                "public_collections",
            ],
        }
        if category or event_format:
            data["event_search"]["tags"] = []
            if category:
                data["event_search"]["tags"].append(category.api_id)
            if event_format:
                data["event_search"]["tags"].append(event_format.api_id)
        if price:
            data["event_search"]["price"] = price

        log.debug(f"  - API URL: {url}")
        log.debug(f"  - API DATA: {json.dumps(data)}")

        r = self.p.session.post(url, json=data, headers=headers)
        data = r.json()

        return data


class EventProfile:
    def __init__(self, parent: "Eventbrite"):
        self.p = parent

    def load(self, url: str) -> dm.Event:
        """
        It takes a eventbrite event URL, loads it and return Event object

        Args:
          url (str): The URL of the event page.

        Returns:
          A dictionary of the event profile
        """
        self.p.waiter.wait_if_needed(self.p.delay_between_fetches)

        # If not URL then it is event id
        if not url.startswith("http"):
            url = URL.event_profile(event_id=url)

        html_content = self.__load_event_page(url)

        data = self.__extract_window_data(html_content)
        event = serialize_event_profile(data)

        return event

    def __load_event_page(self, url: str):
        headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;"
                "q=0.8,application/signed-exchange;"
                "v=b3;q=0.9"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "www.eventbrite.com",
            "Pragma": "no-cache",
            "sec-ch-ua": self.p.headers["sec-ch-ua"],
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": self.p.headers["sec-ch-ua-platform"],
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.p.headers["User-Agent"],
        }

        r = self.p.session.get(url, headers=headers)
        data = r.content.decode("utf-8")

        return data

    @staticmethod
    def __extract_window_data(value: Union[str, lxml.html.HtmlElement]) -> dict:
        """
        Parses data from html block with `window.server_data` in it

        Args:
          value (Union[str, lxml.html.HtmlElement]): The HTML string or
            lxml.html.HtmlElement object to extract the data from.

        Returns:
          A dictionary of the data from the page.
        """
        if isinstance(value, str):
            tree = lxml.html.fromstring(value)
        else:
            tree = value

        raw_results = re.findall(
            r"(?ims)window\.\_\_SERVER_DATA\_\_ \=(.*?\})\;",
            tree.xpath("//script[contains(.,'window.__SERVER_DATA__')]")[0].text,
        )
        try:
            results = json.loads(raw_results[0].strip(), strict=False)
        except json.JSONDecodeError as e:
            log.error(raw_results[0])
            raise e
        return results


class URL:
    base = "https://www.eventbrite.com"

    @classmethod
    def search_page(
        cls,
        region: str,
        dt_start: Union[str, datetime.datetime],
        dt_end: Union[str, datetime.datetime],
        price: Literal["paid", "free"] = None,
        category: dm.D = None,
        event_format: dm.D = None,
        page_n: int = 1,
    ) -> str:

        # URL path
        path = []
        if price:
            path.append(price)
        if category:
            path.append(category.url_id)
        if event_format:
            path.append(event_format.url_id)
        path_encoded = "--".join(path) if path else "all-events"

        # URL params
        params = [("page", page_n)]
        if dt_start and dt_end:
            if isinstance(dt_start, datetime.datetime):
                dt_start = dt_start.strftime("%Y-%m-%d")
            elif not isinstance(dt_start, str):
                raise TypeError(
                    f"dt_start must be datetime or str. Given: {type(dt_start)}"
                )

            if isinstance(dt_end, datetime.datetime):
                dt_end = dt_end.strftime("%Y-%m-%d")
            elif not isinstance(dt_end, str):
                raise TypeError(
                    f"dt_end must be datetime or str. Given: {type(dt_end)}"
                )

            params.append(("start_date", dt_start))
            params.append(("end_date", dt_end))
        params_encoded = "&".join([f"{k}={url_encode(str(v))}" for k, v in params if v])

        url = f"{cls.base}/d/{region}/{path_encoded}/?{params_encoded}"
        return url

    @classmethod
    def search_page_api(cls):
        return f"{cls.base}/api/v3/destination/search/"

    @classmethod
    def event_profile(cls, event_id):
        return f"https://www.eventbrite.com/e/{event_id}"
