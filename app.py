from seleniumbase import SB
import os, sys, json

def bypass_cloudflare(url, wait_for_element=None, sleep=5):
    try:
        with SB(uc=True, test=True, xvfb=True) as sb:
            sb.open(url)
            if wait_for_element:
                sb.wait_for_element_visible(wait_for_element, timeout=30)
            sb.sleep(sleep)
            cookies = sb.driver.get_cookies()
            html = sb.get_page_source()
            return {
                "status": True,
                "html": html,
                "cookies": cookies
            }
    except Exception as e:
        return {"status": False, "message": str(e)}

def main():
    result = bypass_cloudflare(
        "https://dexscreener.com/solana/5xce2hxecqptlfytx5gcmni9lsb8rxyjbw1ex4nby1fq",
        wait_for_element='button[type="button"][title="Lights on"]',
        sleep=5
    )
    if result["status"]:
        with open("page.html", "w", encoding="utf-8") as f:
            f.write(result["html"])
        with open("cookies.json", "w") as f:
            json.dump(result["cookies"], f)
        print("[+] Page and cookies saved.")
    else:
        print(f"[-] Failed: {result['message']}")

if __name__ == "__main__":
    main()
