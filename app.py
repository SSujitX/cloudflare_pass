import asyncio
import nodriver
from nodriver_cf import CFVerify
import json


async def main():
    browser = await nodriver.start()
    page = await browser.get(
        "https://www.legacy.com/api/_frontend/localmarket/united-states/california/subregion/alameda-county"
    )
    await page.save_screenshot("before.png")
    cf_verify = CFVerify(_browser_tab=page, _debug=True)
    verified = await cf_verify.verify()

    if verified:
        print("Cloudflare bypassed successfully.")
        await page.sleep(5)
        await page.save_screenshot("after.png")
        content = await page.get_content()
        with open("content.html", "w", encoding="utf-8") as f:
            f.write(content)

        all_cookies = await browser.cookies.get_all()
        cf_clearance = None
        for cookie in all_cookies:
            if cookie.name == "cf_clearance":
                cf_clearance = cookie.value
                break

        if cf_clearance:
            with open("cf_clearance.json", "w", encoding="utf-8") as f:
                json.dump({"cf_clearance": cf_clearance}, f, indent=4)

    else:
        print("Failed to bypass Cloudflare.")


if __name__ == "__main__":
    asyncio.run(main())
