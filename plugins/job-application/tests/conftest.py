import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def chromium_or_skip():
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(); b.close()
    except Exception:
        pytest.skip("Chromium not installed (run: jobkit install-browser)")
