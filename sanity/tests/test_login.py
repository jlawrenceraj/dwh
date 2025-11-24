from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os
import time
import pytest
import json
from typing import List, Tuple, Optional, Dict, Any
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import requests
from selenium.webdriver.support.ui import WebDriverWait
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


class Config:
    """Configuration container. Reads defaults from env and optional JSON selectors file.

    Environment variables supported:
    - TEST_URL, TEST_USER, TEST_PASS, TEST_EXPECT_URL_CONTAINS
    - HEADLESS (true/false)
    - SCREENSHOT_DIR
    - SELECTORS_FILE (optional JSON path to override selectors)
    - CONFIG_FILE (top-level JSON overriding other values)
    """

    DEFAULT_SELECTORS: Dict[str, List[Tuple[str, str]]] = {
        'username': [
            ('id', 'username'),
            ('name', 'username'),
            ('id', 'email'),
            ('name', 'email'),
            ('css', 'input[type="email"]'),
            ('css', 'input[type="text"]')
        ],
        'password': [
            ('id', 'password'),
            ('name', 'password'),
            ('css', 'input[type="password"]')
        ],
        'submit': [
            ('css', 'button[type="submit"]'),
            ('css', 'input[type="submit"]'),
            ('xpath', "//button[contains(.,'Log') or contains(.,'Sign') or contains(.,'Submit')]")
        ],
        'home': [
            ('link_text', 'Home'),
            ('partial_link_text', 'Home'),
            ('css', 'a.home'),
            ('css', 'a[href="/"]'),
            ('xpath', "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'home')]")
        ],
        'practice': [
            ('link_text', 'Practice'),
            ('partial_link_text', 'Practice'),
            ('css', 'a.practice'),
            ('css', 'a[href*="practice"]'),
            ('xpath', "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'practice')]")
        ]
        ,
        'blog': [
            ('link_text', 'Blog'),
            ('partial_link_text', 'Blog'),
            ('css', 'a.blog'),
            ('css', 'a[href*="blog"]'),
            ('xpath', "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'blog')]")
        ],
        'contact': [
            ('link_text', 'Contact'),
            ('partial_link_text', 'Contact'),
            ('css', 'a.contact'),
            ('css', 'a[href*="contact"]'),
            ('xpath', "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'contact')]")
        ]
    }

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        env = os.environ
        self.url = env.get('TEST_URL', 'http://localhost:8000/login')
        self.user = env.get('TEST_USER', 'user@example.com')
        self.password = env.get('TEST_PASS', 'password')
        self.expect_url_contains = env.get('TEST_EXPECT_URL_CONTAINS', '')
        self.browser = env.get('BROWSER', 'chrome')
        self.headless = env.get('HEADLESS', 'true').lower() not in ('0', 'false', 'no')
        self.screenshot_dir = env.get('SCREENSHOT_DIR', SCREENSHOT_DIR)
        self.selectors_file = env.get('SELECTORS_FILE')
        self.config_file = env.get('CONFIG_FILE')
        # shallow copy of defaults
        self.selectors = dict(self.DEFAULT_SELECTORS)

        if self.selectors_file and os.path.exists(self.selectors_file):
            try:
                with open(self.selectors_file, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                self.selectors = self._parse_selectors_json(raw)
            except Exception:
                # fallback to defaults on error
                pass

        # If a top-level config JSON file is provided, load values from there and override
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                if isinstance(cfg, dict):
                    self.url = cfg.get('url', self.url)
                    self.user = cfg.get('user', self.user)
                    self.password = cfg.get('password', self.password)
                    self.expect_url_contains = cfg.get('expect_url_contains', self.expect_url_contains)
                    if 'headless' in cfg:
                        h = cfg.get('headless')
                        if isinstance(h, bool):
                            self.headless = h
                        elif isinstance(h, str):
                            self.headless = h.lower() not in ('0', 'false', 'no')
                    self.screenshot_dir = cfg.get('screenshot_dir', self.screenshot_dir)
                    if cfg.get('selectors_file'):
                        self.selectors_file = cfg.get('selectors_file')
                    if cfg.get('selectors') and isinstance(cfg.get('selectors'), dict):
                        try:
                            self.selectors = self._parse_selectors_json(cfg.get('selectors'))
                        except Exception:
                            pass
            except Exception:
                pass

        if data:
            for k, v in data.items():
                setattr(self, k, v)

    @staticmethod
    def _parse_selectors_json(raw: Dict[str, Any]) -> Dict[str, List[Tuple[str, str]]]:
        out: Dict[str, List[Tuple[str, str]]] = {}
        for key, items in raw.items():
            lst: List[Tuple[str, str]] = []
            for it in items:
                by = it.get('by') if isinstance(it, dict) else None
                val = it.get('value') if isinstance(it, dict) else None
                if by and val:
                    lst.append((by, val))
            if lst:
                out[key] = lst
        # merge with defaults for missing keys
        for k, v in Config.DEFAULT_SELECTORS.items():
            out.setdefault(k, v)
        return out

    @classmethod
    def from_env(cls) -> 'Config':
        return cls()


class SeleniumHelper:
    def __init__(self, config: Config):
        self.config = config
        os.makedirs(self.config.screenshot_dir, exist_ok=True)
        self.driver = self._create_driver()

    def _create_driver(self):
        browser = getattr(self.config, 'browser', os.environ.get('BROWSER', 'chrome')).lower()
        if browser in ('edge', 'msedge'):
            options = EdgeOptions()
            if self.config.headless:
                # Edge uses same headless arg
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f"--window-size=1280,1024")
            service = EdgeService(EdgeChromiumDriverManager().install())
            drv = webdriver.Edge(service=service, options=options)
            return drv

        # default: chrome
        options = webdriver.ChromeOptions()
        if self.config.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f"--window-size=1280,1024")
        service = ChromeService(ChromeDriverManager().install())
        drv = webdriver.Chrome(service=service, options=options)
        return drv

    def take_screenshot(self, name: str) -> str:
        ts = time.strftime('%Y%m%d-%H%M%S')
        filename = f"{ts}-{name}.png"
        path = os.path.join(self.config.screenshot_dir, filename)
        try:
            self.driver.save_screenshot(path)
        except Exception:
            pass
        return path

    def _by_from_string(self, by: str):
        m = by.lower()
        return {
            'id': By.ID,
            'name': By.NAME,
            'css': By.CSS_SELECTOR,
            'xpath': By.XPATH,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT
        }.get(m, By.CSS_SELECTOR)

    def find_element_any(self, selectors: List[Tuple[str, str]], timeout: float = 5):
        """Try each locator until one is present. Returns the WebElement or raises."""
        end = time.time() + timeout
        last_exc = None
        while time.time() < end:
            for by_str, val in selectors:
                try:
                    by = self._by_from_string(by_str)
                    el = self.driver.find_element(by, val)
                    return el
                except Exception as exc:
                    last_exc = exc
                    continue
            time.sleep(0.2)
        raise NoSuchElementException('No selector matched') from last_exc

    def safe_click(self, element, name_for_screenshot: Optional[str] = None, wait_for_new_window: bool = True):
        before_handles = list(self.driver.window_handles)
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            WebDriverWait(self.driver, 10).until(lambda d: element.is_displayed() and element.is_enabled())
            try:
                element.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", element)
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception:
                pass

        # small wait and handle possible new window/tab
        time.sleep(0.5)
        if wait_for_new_window:
            after_handles = list(self.driver.window_handles)
            if len(after_handles) > len(before_handles):
                self.driver.switch_to.window(after_handles[-1])

        if name_for_screenshot:
            self.take_screenshot(name_for_screenshot)

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass


class ApplicationTest:
    def __init__(self, helper: SeleniumHelper, config: Config):
        self.h = helper
        self.config = config

    def open(self):
        # quick reachability check to fail-fast and skip when the app server isn't running
        try:
            resp = urlopen(self.config.url, timeout=3)
            try:
                resp.close()
            except Exception:
                pass
        except (URLError, HTTPError) as e:
            reason = getattr(e, 'reason', e)
            pytest.skip(f"Target URL not reachable: {self.config.url} ({reason})")

        self.h.driver.get(self.config.url)
        self.h.take_screenshot('page_loaded')

    def login(self):
        sel = self.config.selectors
        user_el = self.h.find_element_any(sel['username'])
        pass_el = self.h.find_element_any(sel['password'])
        user_el.clear()
        user_el.send_keys(self.config.user)
        pass_el.clear()
        pass_el.send_keys(self.config.password)
        self.h.take_screenshot('filled')
        submit_el = self.h.find_element_any(sel['submit'])
        self.h.safe_click(submit_el, 'after_submit')

    def click_home(self):
        try:
            el = self.h.find_element_any(self.config.selectors['home'])
            self.h.safe_click(el, 'home_clicked')
            return True
        except NoSuchElementException:
            self.h.take_screenshot('home_not_found')
            return False

    def click_practice(self):
        try:
            el = self.h.find_element_any(self.config.selectors['practice'])
            self.h.safe_click(el, 'practice_clicked')
            return True
        except NoSuchElementException:
            self.h.take_screenshot('practice_not_found')
            return False

    def click_blog(self):
        try:
            el = self.h.find_element_any(self.config.selectors['blog'])
            self.h.safe_click(el, 'blog_clicked')
            return True
        except NoSuchElementException:
            self.h.take_screenshot('blog_not_found')
            return False

    def click_contact(self):
        try:
            el = self.h.find_element_any(self.config.selectors['contact'])
            self.h.safe_click(el, 'contact_clicked')
            return True
        except NoSuchElementException:
            self.h.take_screenshot('contact_not_found')
            return False


@pytest.fixture
def driver():
    cfg = Config.from_env()
    helper = SeleniumHelper(cfg)
    yield helper.driver
    try:
        helper.quit()
    except Exception:
        pass


@pytest.fixture
def app():
    cfg = Config.from_env()
    # ensure target URL is reachable before creating browser
    try:
        resp = requests.get(cfg.url, timeout=3)
        resp.raise_for_status()
    except Exception as e:
        pytest.skip(f"Target URL {cfg.url} unreachable: {e}")
    helper = SeleniumHelper(cfg)
    app = ApplicationTest(helper, cfg)
    yield app
    helper.quit()


def test_login_flow(app: ApplicationTest, driver):
    # keep driver fixture present so conftest can capture screenshots on failure
    cfg = app.config
    app.open()
    app.login()

    # optional expectation check
    if cfg.expect_url_contains:
        WebDriverWait(app.h.driver, 5).until(lambda d: cfg.expect_url_contains in d.current_url)
    else:
        assert app.h.driver.current_url != cfg.url

    # click home (tolerant)
    app.click_home()

    # click practice (tolerant)
    app.click_practice()

    # click blog and contact (tolerant)
    app.click_blog()
    app.click_contact()
