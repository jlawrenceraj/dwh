<#
Simple helper to run the Selenium tests on Windows (PowerShell).
Edit the variables below or pass them into the environment before running.
Usage:
  .\run_tests_windows.ps1
#>

param(
    [string]$TestUrl = "https://practicetestautomation.com/practice-test-login/",
    [string]$TestUser = "student",
    [string]$TestPass = "Password123",
    [string]$ExpectContains = ""
)

if (Test-Path .venv\Scripts\Activate.ps1) {
    Write-Host "Activating .venv..."
    <#  . .\venv\Scripts\Activate.ps1  #>
} else {
    Write-Host "Virtualenv not found. Creating .venv and installing requirements..."
    python -m venv .venv
    . .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
}

$env:TEST_URL = $TestUrl
$env:TEST_USER = $TestUser
$env:TEST_PASS = $TestPass
if ($ExpectContains -ne "") { $env:TEST_EXPECT_URL_CONTAINS = $ExpectContains }

pytest -q
