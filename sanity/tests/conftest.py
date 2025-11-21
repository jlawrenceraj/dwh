import os
import time
import pytest


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == 'call' and rep.failed:
        driver = item.funcargs.get('driver', None)
        if driver:
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            path = os.path.join(screenshot_dir, f'failure-{time.strftime("%Y%m%d-%H%M%S")}.png')
            try:
                driver.save_screenshot(path)
            except Exception:
                pass
