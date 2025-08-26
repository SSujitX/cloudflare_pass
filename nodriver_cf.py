import asyncio
from datetime import datetime
from typing import Optional, Any
import nodriver


class CFLogger:
    def __init__(self, _class_name: str, _debug: bool = False) -> None:
        self.debug: bool = _debug
        self.class_name: str = _class_name

    async def log(self, _message: str) -> None:
        if not self.debug:
            return

        print(
            f"({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) [{self.class_name}]: {_message}"
        )


class CFUtil:
    def __init__(self, _browser_tab: nodriver.Tab, _debug=False) -> None:
        self.debug: bool = _debug
        self.browser_tab: nodriver.Tab = _browser_tab
        self.cf_logger: CFLogger = CFLogger(
            _class_name=self.__class__.__name__, _debug=self.debug
        )

    async def create_instance_id(self, _max_retries: int = 10) -> Optional[str]:
        for retry_count in range(1, _max_retries + 1):
            target_id: Optional[str] = self.browser_tab.target.target_id
            target_url: Optional[str] = self.browser_tab.target.url

            if "://" in target_url:
                target_url = target_url.split("/")[2]

            if not target_id or not target_url:
                await asyncio.sleep(0.05)
                continue

            instance_id: Optional[str] = f"{target_id[-5:]}-{target_url}"
            await self.cf_logger.log(f"Created instance_id: {instance_id}")
            return instance_id

        await self.cf_logger.log(f"instance_id could not be created.")

    async def run_js(self, javascript: str, return_value: bool = True) -> Any:
        result: Any = await self.browser_tab.evaluate(expression=javascript)

        if not return_value:
            return

        if not isinstance(result, list):
            return result

        results = []
        for value in result:
            if not isinstance(value, dict):
                results.append(value)
                continue

            results.append(value["value"])

        return results


class CFHelper:
    def __init__(self, _browser_tab: nodriver.Tab, _debug: bool = False) -> None:
        self.debug: bool = _debug
        self.browser_tab: nodriver.Tab = _browser_tab

        self.cf_util: CFUtil = CFUtil(self.browser_tab, _debug=self.debug)
        self.cf_logger: CFLogger = CFLogger(
            _class_name=self.__class__.__name__, _debug=self.debug
        )

    async def is_cloudflare_presented(
        self, _max_retries: int = 5, _interval_between_retries: float = 0.1
    ) -> bool:
        obv_things: list[str] = [
            "challenges.cloudflare.com",
            "cdn-cgi/challenge-platform",
            "turnstile/v0/api.js",
        ]
        urls: list[str] = []

        for i in range(_max_retries):
            for i in range(5):
                try:
                    if "turnstile" in await self.browser_tab.evaluate("document.title"):
                        return True

                    urls: list[str] = await self.cf_util.run_js(
                        "[...document.querySelectorAll('script[src]')].map(script => script.src)",
                        return_value=True,
                    )

                    if not urls:
                        continue

                    break

                except Exception as e:
                    await self.cf_logger.log(
                        f"Error occured while fetching urls from site: {e}"
                    )

                await asyncio.sleep(0.1)

            if len(urls) == 0:
                await self.cf_logger.log(f"No urls were fetched from site.")
                continue

            for thing in obv_things:
                for url in urls:
                    if thing in url:
                        return True

            await asyncio.sleep(delay=_interval_between_retries)

        return False

    async def find_cloudflare_iframe(self) -> Optional[nodriver.Element]:
        try:
            iframes: list[nodriver.Element] = [
                iframe
                for iframe in await self.browser_tab.find_all("iframe")
                if iframe.attrs.get("src")
            ]

            for iframe in iframes:
                iframe_id: str = iframe.attrs.get("id", "").lower()
                iframe_class: str = iframe.attrs.get("class", "").lower()

                if (
                    "cf-" in iframe_id
                    or "turnstile" in iframe_id
                    or "cf-" in iframe_class
                ):
                    await self.cf_logger.log(
                        f"Found potential Cloudflare iframe with {'id=' + iframe_id if iframe_id else ''}"
                        f"{' and ' if iframe_id and iframe_class else ''}"
                        f"{'class=' + iframe_class if iframe_class else ''}"
                    )
                    return iframe

        except Exception as e:
            await self.cf_logger.log(f"Error occurred: {e}")


class CFVerify:
    def __init__(self, _browser_tab: nodriver.Tab, _debug: bool = False) -> None:
        if not isinstance(_browser_tab, nodriver.Tab):
            raise ValueError(
                f"_browser_tab parameter must be an instance of nodriver.Tab."
            )

        if not isinstance(_debug, bool):
            raise ValueError(f"_debug parameter must be a bool.")

        self.debug: bool = _debug
        self.browser_tab: nodriver.Tab = _browser_tab
        self.instance_id: Optional[str] = None

        self.cf_util: CFUtil = CFUtil(_browser_tab=self.browser_tab, _debug=self.debug)
        self.cf_helper: CFHelper = CFHelper(
            _browser_tab=self.browser_tab, _debug=self.debug
        )
        self.cf_logger: CFLogger = CFLogger(self.__class__.__name__, _debug=self.debug)

    async def log(self, message: str) -> None:
        if not self.instance_id:
            self.instance_id = await self.cf_util.create_instance_id()

        await self.cf_logger.log(f"<{self.instance_id}>: {message}")

    async def verify(
        self,
        _max_retries=10,
        _interval_between_retries=1,
        _reload_page_after_n_retries=0,
    ) -> bool:
        await self.log("Verifying cloudflare has started.")

        for retry_count in range(1, _max_retries + 1):
            await self.log(
                f"Trying to verify cloudflare. Attempt {retry_count} of {_max_retries}."
            )

            await asyncio.sleep(delay=_interval_between_retries)

            if (
                retry_count < _max_retries
                and _reload_page_after_n_retries > 0
                and retry_count % _reload_page_after_n_retries == 0
            ):
                await self.log(
                    f"Reloading page... Attempt {retry_count} of {_max_retries}, reload interval {_reload_page_after_n_retries}."
                )
                await self.browser_tab.reload()
                continue

            if not await self.cf_helper.is_cloudflare_presented():
                await self.log(
                    f"Cloudflare is not presented on site. No verify needed."
                )
                return True

            iframe: Optional[nodriver.Element] = (
                await self.cf_helper.find_cloudflare_iframe()
            )

            if not iframe:
                await self.log("No cloudflare iframe found.")

                if not await self.cf_helper.is_cloudflare_presented():
                    await self.log(
                        "Cloudflare has been verified successfully (no iframe required)."
                    )
                    return True

                continue

            try:
                await iframe.mouse_click()
                await self.log("Cloudflare iframe has been clicked.")

            except Exception as e:
                await self.log(f"Error while clicking iframe: {e}")

                if "could not find position for" in str(e):
                    await self.log(f"Cloudflare iframe could not load properly.")
                    continue

                if not await self.cf_helper.is_cloudflare_presented():
                    await self.log(
                        "Cloudflare has been verified successfully despite error."
                    )
                    return True

        if await self.cf_helper.is_cloudflare_presented():
            await self.log("Cloudflare could not be verified for an unknown reason.")
            return False

        await self.log("Cloudflare has been verified successfully.")
        return True
