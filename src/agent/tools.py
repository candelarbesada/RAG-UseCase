from typing import Any
import re

import requests
from langchain_core.tools import tool

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError as exc:
        raise ImportError("Install package `ddgs` to use the web search tool.") from exc


class DuckDuckGoSearchRun:
    name = "web_search"
    description = "Performs a duckduckgo web search based on your query (think a Google search) then returns the top search results."
    inputs = {'query': {'type': 'string', 'description': 'The search query to perform.'}}
    output_type = "string"

    def __init__(self, max_results=10, **kwargs):
        self.max_results = max_results
        self.ddgs = DDGS(**kwargs)

    def forward(self, query: str) -> str:
        results = self.ddgs.text(query, max_results=self.max_results)
        if len(results) == 0:
            raise Exception("No results found! Try a less restrictive/shorter query.")
        postprocessed_results = [f"[{result['title']}]({result['href']})\n{result['body']}" for result in results]
        return "## Search Results\n\n" + "\n\n".join(postprocessed_results)


class VisitWebpageTool:
    name = "visit_webpage"
    description = "Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
    inputs = {'url': {'type': 'string', 'description': 'The url of the webpage to visit.'}}
    output_type = "string"

    def forward(self, url: str) -> str:
        try:
            from markdownify import markdownify
            from requests.exceptions import RequestException
        except ImportError as e:
            raise ImportError(
                "You must install packages `markdownify` and `requests` to run this tool: for instance run `pip install markdownify requests`."
            ) from e
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            markdown_content = markdownify(response.text).strip()
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

            return truncate_content(markdown_content, 10000)

        except requests.exceptions.Timeout:
            return "The request timed out. Please try again later or check the URL."
        except RequestException as e:
            return f"Error fetching the webpage: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def __init__(self, *args, **kwargs):
        self.is_initialized = False


@tool
def get_weather(location: str, when: str = "today") -> str:
    """Get real weather info for a city using Open-Meteo."""
    if not location or not location.strip():
        return "Please provide a valid location."

    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        geo.raise_for_status()
        results = geo.json().get("results")

        if not results:
            return f"I could not find weather data for '{location}'."

        place = results[0]
        lat = place["latitude"]
        lon = place["longitude"]
        city = place.get("name", location)
        country = place.get("country", "")

        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=12,
        )
        forecast.raise_for_status()
        data = forecast.json()

        current = data.get("current", {})
        temp = current.get("temperature_2m")
        feels_like = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        return (
            f"Weather in {city}, {country} ({when}): "
            f"{temp}°C, feels like {feels_like}°C, humidity {humidity}%, wind {wind} km/h."
        )

    except requests.RequestException as exc:
        return f"The weather service failed for '{location}': {exc}"


@tool
def search_tool(query: str) -> str:
    """Search the web for a query and return the top results."""
    return DuckDuckGoSearchRun().forward(query)


@tool
def visit_webpage_tool(url: str) -> str:
    """Visit a webpage and return its markdown content."""
    return VisitWebpageTool().forward(url)


def truncate_content(text: str, max_length: int = 10000) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."
