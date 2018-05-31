import inspect
import aiohttp


class HTTPProxy:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    def __del__(self):
        self.session.close()

    async def _func(self, method: str, url: str, attribute: str = "text", **kwargs):
        func = getattr(self.session, method)
        async with func(url, **kwargs) as response:
            assert 200 <= response.status < 300
            attr = getattr(response, attribute)
            if inspect.isfunction(attr):
                attr = attr()

            if inspect.isawaitable(attr):
                attr = await attr

            return attr

    def get(self, *args, **kwargs):
        return self._func("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._func("post", *args, **kwargs)


proxy = HTTPProxy()


def get(*args, **kwargs):
    return proxy.get(*args, **kwargs)


def post(*args, **kwargs):
    return proxy.post(*args, **kwargs)
