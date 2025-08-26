import asyncio

import zendriver as zd


async def main():
    browser = await zd.start()
    page = await browser.get("https://www.browserscan.net/bot-detection")
    await page.sleep(5)
    await page.save_screenshot("after.png")
    await page.sleep(5)
    await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
