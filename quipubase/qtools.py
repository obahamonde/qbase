import asyncio
import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from bs4 import BeautifulSoup  # pylint: disable=E0401
from fastapi import APIRouter, Body, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pyppeteer import browser, launch  # type: ignore

from .qproxy import QProxy
from .qschemas import create_class  # type: ignore
from .qschemas import JsonSchema
from .qutils import get_logger

chrome: browser.Browser = None  # type: ignore
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

    query: str = Field(..., description="The query to search for.")

    async def _run(self, *, chrome_: browser.Browser) -> list[str]:
        page = await chrome_.newPage()  # type: ignore
        await page.setUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
        await page.goto("https://www.google.com")  # type: ignore
        await page.type("input[name=q]", self.query)  # type: ignore
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

    async def _browse(self, **kwargs: Any):
        """Runs the Google search and returns the URLs of the search results."""
        global chrome
        if not chrome:
            chrome = await launch(
                headless=True,
                args=["--no-sandbox"],
            )
        try:
            urls = await self._run(chrome_=chrome)
            content = await asyncio.gather(
                *[self._fetch(url=url, chrome_=chrome) for url in urls]
            )
            for k, v in zip(urls, content):
                result = GoogleResult(url=k, content=v)
                yield result
        except (RuntimeError, KeyError) as e:
            logger.error("Error running Google search: %s", e)
            raise HTTPException(status_code=500, detail="Error running search.") from e
        finally:
            await chrome.close()

    async def _fetch(self, *, url: str, chrome_: browser.Browser) -> str:
        page = await chrome_.newPage()
        try:
            await page.goto(url)  # type: ignore
            content = await page.content()  # type: ignore
            return BeautifulSoup(content, "lxml").get_text().strip()
        except (RuntimeError, KeyError):
            return ""
        finally:
            await page.close()  # type: ignore

    async def run(self, **kwargs: Any) -> list[GoogleResult]:
        return [i async for i in self._browse(**kwargs)]


class SyntheticDataTool(Tool, QProxy[AsyncOpenAI]):
    """Generates synthetic data based on a given schema."""

    json_schema: JsonSchema = Field(
        ..., description="The JSON schema of the data to generate."
    )
    n_of_samples: int = Field(
        default=10, description="The number of samples to generate."
    )
    instruction: str = Field(
        default="Generate synthetic data based on the given schema.",
        description="The instruction to be passed to the model.",
    )

    async def run(self, **kwargs: Any):
        n = self.n_of_samples
        model = create_class(
            schema=self.json_schema, base=SyntheticDataTool, action=None
        )
        PROMPT = f"""You are a synthetic data generator, generate exactly {n} samples according to the following schema: {model.model_json_schema()}. Output them as a json object in a the following format:
		{{"data": [*samples]}}
		The output must be valid `json` with no backticks neither additional or prior content or advicce.
		"""
        response = await self.__load__().chat.completions.create(
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": self.instruction},
            ],
            model="llama3-8B-8192",
            max_tokens=8192,
            functions=[self.json_schema],  # type: ignore
        )
        call = response.choices[0].message.function_call
        content = response.choices[0].message.content
        if not call and not content:
            raise HTTPException(status_code=500, detail="No response from the model.")
        if call:
            arguments = json.loads(call.arguments)["data"]
        elif content:
            arguments = json.loads(content)["data"]
        else:
            raise HTTPException(status_code=500, detail="No response from the model.")
        return [
            model.model_validate(s).model_dump_json() for s in arguments  # type: ignore
        ]

    def __load__(self):
        return AsyncOpenAI(base_url=os.environ["OPENAI_BASE_URL"])


app = APIRouter(tags=["tool"], prefix="/tools")


@app.post("/search")
async def search(tool: BrowsingTool = Body(...)):
    return await tool.run()


@app.post("/synthetic")
async def synthetic(tool: SyntheticDataTool = Body(...)):
    return await tool.run()
