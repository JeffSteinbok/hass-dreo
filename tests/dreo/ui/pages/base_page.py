"""
Base page object for Home Assistant UI pages.
Provides common functionality for all page objects.
"""
from playwright.sync_api import Page, expect


class BasePage:
    """Base class for all page objects."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def navigate_to(self, url: str):
        """Navigate to a URL."""
        self.page.goto(url)
    
    def wait_for_element(self, selector: str, timeout: int = 30000):
        """Wait for an element to be visible."""
        self.page.wait_for_selector(selector, timeout=timeout)
    
    def click(self, selector: str):
        """Click an element."""
        self.page.click(selector)
    
    def fill(self, selector: str, text: str):
        """Fill an input field."""
        self.page.fill(selector, text)
    
    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self.page.text_content(selector)
    
    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return self.page.is_visible(selector)
    
    def wait_for_navigation(self, timeout: int = 30000):
        """Wait for navigation to complete."""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
