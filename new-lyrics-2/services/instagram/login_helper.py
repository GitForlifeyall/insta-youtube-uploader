"""
Instagram Chrome Login Helper
Launches a Chrome browser window for user to log in, captures cookies,
and exports settings into ig_session.json for instagrapi.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from instagrapi import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ig_login_helper")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SESSION_FILE = ROOT_DIR / "ig_session.json"

def launch_chrome_login(timeout_seconds: int = 300) -> bool:
    """
    Opens Chrome for the user to log into Instagram.
    Polls until login cookies (sessionid, ds_user_id) are present.
    """
    logger.info("Starting Chrome for Instagram login...")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.error(f"Failed to launch Chrome with webdriver-manager: {e}. Falling back to default PATH chrome...")
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e2:
            logger.error(f"Chrome launch failed: {e2}")
            return False

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        logger.info("Opened Instagram login page. Please log in within the Chrome window.")

        start_time = time.time()
        logged_in = False
        captured_cookies = {}

        while time.time() - start_time < timeout_seconds:
            time.sleep(2)
            try:
                cookies = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                # Check for crucial session cookies
                if "sessionid" in cookie_dict:
                    sessionid = cookie_dict["sessionid"]
                    if len(sessionid) > 20:
                        logged_in = True
                        captured_cookies = cookie_dict
                        logger.info("Detected sessionid cookie in Chrome!")
                        break
            except Exception as e:
                # Browser might be navigating or closed
                if "no such window" in str(e).lower() or "target window already closed" in str(e).lower():
                    logger.warning("Browser window was closed by user.")
                    break

        if logged_in:
            logger.info("Extracting and initializing instagrapi Client with sessionid...")
            sessionid = captured_cookies.get("sessionid")
            
            cl = Client()
            cl.delay_range = [1, 3]
            try:
                cl.login_by_sessionid(sessionid)
                logger.info(f"Instagrapi successfully logged in as user ID: {cl.user_id}")
            except Exception as login_err:
                logger.warning(f"login_by_sessionid raised: {login_err}. Populating cookies manually...")
                cl.set_settings({})
                cl.set_cookie("sessionid", sessionid)
                if "ds_user_id" in captured_cookies:
                    cl.set_cookie("ds_user_id", captured_cookies["ds_user_id"])
                    cl.user_id = str(captured_cookies["ds_user_id"])
                if "csrftoken" in captured_cookies:
                    cl.set_cookie("csrftoken", captured_cookies["csrftoken"])
                if "mid" in captured_cookies:
                    cl.set_cookie("mid", captured_cookies["mid"])
                if "ig_did" in captured_cookies:
                    cl.set_cookie("ig_did", captured_cookies["ig_did"])
                if "rur" in captured_cookies:
                    cl.set_cookie("rur", captured_cookies["rur"])

            cl.dump_settings(str(SESSION_FILE))
            logger.info(f"Successfully saved Instagram session to {SESSION_FILE.absolute()}")
            time.sleep(1)
            driver.quit()
            return True
        else:
            logger.warning("Timed out or login was not completed.")
            driver.quit()
            return False

    except Exception as err:
        logger.error(f"Error during Chrome login: {err}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    success = launch_chrome_login()
    if success:
        print(json.dumps({"status": "success", "message": "Instagram login successful and session saved."}))
        sys.exit(0)
    else:
        print(json.dumps({"status": "error", "message": "Failed to log in or login timed out."}))
        sys.exit(1)
