import asyncio
import re
from abc import ABC, abstractmethod
from typing import Any

from bs4 import BeautifulSoup  # pylint: disable=E0401
from fastapi import APIRouter
from pydantic import BaseModel, Field
from pyppeteer import browser, launch  # type: ignore

from .qutils import get_logger

logger = get_logger(__name__)


class Tool(BaseModel, ABC):
	@classmethod
	def definition(cls):
		return

	@abstractmethod
	async def run(self, **kwargs: Any) -> Any:
		raise NotImplementedError


class GoogleResult(BaseModel):
	"""A single result from a Google search."""

	url: str = Field(..., description="The URL of the search result.")
	content: str = Field(..., description="The content of the search result.")


class BrowsingTool(Tool):
	"""Performs a Google search and returns the URLs of the search results."""

	inputs: str = Field(..., description="The query to search for.")

	async def _run(self, *, chrome_: browser.Browser) -> list[str]:

		page = await chrome_.newPage()  # type: ignore
		await page.setUserAgent(
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
		)
		await page.goto("https://www.google.com")  # type: ignore
		await page.type("input[name=q]", self.inputs)  # type: ignore
		await page.keyboard.press("Enter")  # type: ignore
		await page.waitForNavigation()  # type: ignore
		content = await page.content()  # type: ignore
		soup = BeautifulSoup(content, "lxml")
		links = soup.find_all("a")
		non_empty_links = [link.get("href") for link in links if link.get("href")]
		urls: list[str] = [
			re.search(r"(?P<url>https?://[^\s]+)", link)["url"].split("&")[0]  # type: ignore
			for link in non_empty_links
			if re.search(r"(?P<url>https?://[^\s]+)", link)
		]
		for url in urls:
			if "google.com" in url:
				urls.remove(url)
		return urls

	async def run(self, **kwargs:Any) -> list[GoogleResult]:
		"""Runs the Google search and returns the URLs of the search results."""
		chrome = await launch(
				headless=True,
				args=["--no-sandbox","--remote-debugging-port=5000"]
			)
		try:
			urls = await self._run(chrome_=chrome)
			content = await asyncio.gather(
				*[self._get_content(url=url, chrome_=chrome) for url in urls]
			)
			return [
				GoogleResult(url=url, content=content)
				for url, content in zip(urls, content)
			]
		except (RuntimeError, KeyError) as e:
			logger.error("Error running Google search: %s", e)
			return []
		finally:
			await chrome.close()

	async def _get_content(self, *, url: str, chrome_: browser.Browser) -> str:
		page = await chrome_.newPage()
		try:
			await page.goto(url)  # type: ignore
			content = await page.content()  # type: ignore
			return BeautifulSoup(content, "lxml").get_text().strip()
		except (RuntimeError, KeyError):
			return ""
		finally:
			await page.close()  # type: ignore


app = APIRouter(prefix="/tools", tags=["tools"])

@app.post("/search")
async def search(q:str): # type: ignore
    return await BrowsingTool(inputs=q).run()
