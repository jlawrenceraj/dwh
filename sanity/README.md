Sanity Selenium Login Test

This repository provides a minimal Selenium-based sanity test for a web application's login flow, intended to run in a Linux environment.

Quick setup (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y wget curl unzip gnupg
# Install Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# create and activate virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Environment variables

- `TEST_URL`: full URL to the login page (default: `http://localhost:8000/login`).
- `TEST_USER`: login username/email (default: `user@example.com`).
- `TEST_PASS`: login password (default: `password`).
- `TEST_EXPECT_URL_CONTAINS`: optional string expected to be in the post-login URL (used for simple success check).

External configuration files

- `CONFIG_FILE`: optional path to a JSON file containing top-level configuration. Supported keys: `url`, `user`, `password`, `expect_url_contains`, `headless`, `screenshot_dir`, `selectors_file`, `selectors` (inline selectors object).
- `SELECTORS_FILE`: optional path to a JSON file containing selectors for `username`, `password`, `submit`, `home`, `practice`, `blog`, and `contact`.

Run the test

```bash
# from repository root
source .venv/bin/activate
pytest -q
```

Where screenshots are saved

- Screenshots are written to `data/screenshots/` with timestamps. Tests automatically save a screenshot after page load, after filling the form, after submit, and on failure.

Using config files

1) Create a JSON file that contains any of the supported top-level keys (for example, `config.json`).
2) You can provide selectors inline in `config.json` under the `selectors` key, or supply a separate `SELECTORS_FILE` path pointing to a selectors JSON file.
3) Tell the test runner which file to use by exporting `CONFIG_FILE` or `SELECTORS_FILE`.

Example (Linux):

```bash
export CONFIG_FILE=./config.json
pytest -q
```

Example (PowerShell):

```powershell
$env:CONFIG_FILE = '.\\config.json'
pytest -q
```

Customize

- Update selectors inside `tests/test_login.py` to match your app's login form fields and submit buttons.

Windows setup (PowerShell)

If you're running tests on Windows, these instructions assume you have Python 3.8+ installed and Google Chrome available.

1) Install Chrome (if needed):

 - Install via Chocolatey (recommended):

```powershell
choco install -y googlechrome
```

 - Or download from: https://www.google.com/chrome/

2) Create and activate virtualenv, then install dependencies:

```powershell
# from repository root (PowerShell)
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

3) Run tests (PowerShell) — set environment variables and run `pytest`:

```powershell
# example (PowerShell)
$env:TEST_URL = 'http://localhost:8000/login'
$env:TEST_USER = 'user@example.com'
$env:TEST_PASS = 'password'
# optional: $env:TEST_EXPECT_URL_CONTAINS = '/dashboard'
pytest -q
```

Notes

- `webdriver-manager` will automatically download the matching ChromeDriver for the installed Chrome version on Windows and Linux.
- If you need to run non-headless for debugging, set `HEADLESS=false` in your env or config file, or edit `tests/test_login.py` to remove the `--headless=new` option.
