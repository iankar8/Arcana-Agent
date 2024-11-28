# interface_layer/interface_layer.py

import aiohttp

class InterfaceLayer:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def fetch_data(self, url, params=None):
        async with self.session.get(url, params=params) as response:
            return await response.json()

    async def close(self):
        await self.session.close()