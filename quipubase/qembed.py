import os

import numpy as np
from httpx import AsyncClient

from .qproxy import QProxy

EMBEDDINGS_URL = os.environ["EMBEDDINGS_URL"]


class EmbeddingAPI(QProxy[AsyncClient]):
    def __load__(self):
        return AsyncClient(
            timeout=30,
        )

    async def encode(self, text: str | list[str]):
        if isinstance(text, str):
            text = [text]
        response = await self.__load__().post(EMBEDDINGS_URL, json={"content": text})
        vector = response.json()["content"]
        return np.array(vector)
