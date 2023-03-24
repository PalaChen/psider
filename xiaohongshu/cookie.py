import json
import time
import random
from playwright.sync_api import sync_playwright


def get_cookie(user_agent):
    li=['6401644f0000000013030751',
        '5ecfa6c9000000000101f9ff',
        '62c55057000000000d03a110',
        '63b8097f000000001f01145b',
        '63fb83e5000000001300a2d1',
        '61656b2c0000000021034b57',
        '6401644f0000000013030751',
        '640807240000000013015a4a',
        ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent)
        context.add_init_script(path='stealth.min.js')
        page = context.new_page()

        page.goto(f"https://www.xiaohongshu.com/explore/{random.choice(li)}?source=question")
        time.sleep(6)
        return context.cookies()

def get_cookie_str(cookies) -> str:
    cookie = ""
    if isinstance(cookies, dict):
        for k, v in cookies.items():
            cookie += f"{k}={v}; "
    elif isinstance(cookies, list):
        for t in cookies:
            cookie += f"{t['name']}={t['value']}; "


    return cookie

# if __name__ == '__main__':
#     user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
#     print(get_cookie_str(get_cookie(user_agent)))


