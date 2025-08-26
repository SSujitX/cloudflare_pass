from seleniumbase import SB
import sys
import os

root_path = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir(root_path)

with SB(uc=True, xvfb=True) as sb:
    sb.activate_cdp_mode("https://pikbest.com/")
    sb.sleep(10)
    sb.cdp.save_screenshot("before.png")
    sb.uc_gui_click_captcha()
    sb.sleep(10)
    sb.cdp.save_screenshot("after.png")
    sb.cdp.sleep(2)
    cookies = sb.cdp.get_all_cookies()
    with open("cf_clearance.txt", "w") as f:
        for cookie in cookies:
            # print(cookie["name"])
            if cookie.name == "cf_clearance":
                f.write(cookie.value)