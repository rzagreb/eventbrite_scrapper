from typing import Union, Tuple
import logging
import time
import random


class WaitManager:
    """Creates additional delays for scrapper to avoid ban"""

    def __init__(
        self,
        default_delay_sec: Union[int, Tuple[int, int]] = None,
        start=False,
    ):
        """
        Initiate WaitManager

        Args:
          default_delay_sec (Union[int, Tuple[int, int]]): The default delay in seconds.
            - If a tuple is passed, the delay will be a random number between the two
            values.
          start: If True, the timer will start immediately. Defaults to False
        """
        self.log = logging.getLogger("waiter")
        self.time = None

        self.default_delay_sec = default_delay_sec

        if start:
            self.reset()

    def reset(self):
        self.time = time.monotonic()

    def wait_if_needed(self, sec: Union[int, Tuple[int, int]] = None) -> int:
        """
        If the time since the last call to `reset()` is less than `sec`, then wait
        for `sec` seconds

        Args:
          sec (Union[int, Tuple[int, int]]): The number of seconds to wait. If not
            specified, the default delay is used.

        Returns:
          The difference between the current time and the time the timer was last reset.
        """
        if not self.time:
            self.reset()
            return 0

        diff = time.monotonic() - self.time

        sec = sec if sec else self.default_delay_sec
        if not sec:
            raise ValueError(f"{sec} ({type(sec)})")

        if isinstance(sec, int):
            sec_to_wait = sec
        elif isinstance(sec, tuple):
            sec_to_wait = round(random.uniform(sec[0], sec[1]), 2)
        else:
            raise TypeError(f"{sec} ({type(sec)})")

        if diff < sec_to_wait:
            self.log.debug(f"waiting for {sec_to_wait} seconds...")
            time.sleep(sec_to_wait)

        self.reset()
        return diff
