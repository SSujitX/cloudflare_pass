from seleniumbase import SB
import sys
import os
import json

root_path = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir(root_path)

with SB(uc=True, xvfb=True) as sb:
    sb.activate_cdp_mode(
        "https://www.legacy.com/api/_frontend/localmarket/united-states/california/subregion/alameda-county"
    )
    sb.sleep(10)
    sb.cdp.save_screenshot("before.png")
    sb.sleep(5)
    sb.uc_gui_click_captcha()
    sb.sleep(5)
    sb.cdp.save_screenshot("after.png")
    sb.cdp.sleep(2)
    page_source = sb.cdp.get_page_source()
    with open("content.html", "w", encoding="utf-8") as f:
        f.write(page_source)
    # cookies = sb.cdp.get_all_cookies()

    # with open("cf_clearance.json", "w", encoding="utf-8") as f:
    #     json.dump(cookies, f, indent=4)
