from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")
version = (here / "VERSION").read_text(encoding="utf-8")

setup(
    name="eventbrite-scrapper",
    version=version,
    description="Eventbrite Scrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rzagreb/eventbrite-scrapper",
    author="Roman Zagrebnev",
    keywords=["eventbrite", "events", "scrapper"],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["requests", "lxml", "pytz"],
)
