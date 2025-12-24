"""
Page object for Home Assistant login page.
"""
import time
from .base_page import BasePage


class LoginPage(BasePage):
    """Home Assistant login page object."""
    
    # Selectors
    USERNAME_INPUT = 'input[name="username"]'
    PASSWORD_INPUT = 'input[name="password"]'
    LOGIN_BUTTON = 'button[type="submit"]'
    LOGIN_BUTTON_ALT = 'button:has-text("Next")'  # Alternative for auth page
    LOGIN_BUTTON_ALT2 = 'button:has-text("Log in")'
    ERROR_MESSAGE = '.error'
    AUTHORIZE_BUTTON = 'button:has-text("Authorize")'
    SIDEBAR = 'ha-sidebar'
    
    def __init__(self, page, ha_url: str):
        super().__init__(page)
        self.ha_url = ha_url
    
    def navigate(self):
        """Navigate to the login page."""
        self.navigate_to(self.ha_url)
        # Wait for either login form or sidebar (already logged in)
        time.sleep(2)  # Let page load
        
        # Check if already logged in or on authorize page
        if self.is_visible(self.SIDEBAR):
            return  # Already logged in
        
        if self.is_visible(self.AUTHORIZE_BUTTON):
            # On OAuth authorization page, click authorize
            self.click(self.AUTHORIZE_BUTTON)
            time.sleep(2)
            return
        
        # Wait for login form to appear
        self.wait_for_element(self.USERNAME_INPUT, timeout=10000)
    
    def login(self, username: str, password: str):
        """
        Perform login with username and password.
        
        Args:
            username: Home Assistant username
            password: Home Assistant password
        """
        # Debug: print current URL
        print(f"Current URL: {self.page.url}")
        
        # Check if we're on the authorization page (highest priority)
        if "/auth/authorize" in self.page.url:
            print("On OAuth authorization page")
            # Need to login first if not logged in, then authorize
            # The authorization page might have a login form OR an authorize button
            
            # If there's an authorize button (already logged in), click it
            if self.is_visible(self.AUTHORIZE_BUTTON):
                print("Authorize button visible, clicking...")
                self.click(self.AUTHORIZE_BUTTON)
                time.sleep(3)
                print(f"After authorize click, URL: {self.page.url}")
                return
            
            # Otherwise, we need to login on the authorization page
            print("Need to login on authorization page...")
            # Continue to login below
        
        # Check if already logged in
        if self.is_visible(self.SIDEBAR):
            print("Already logged in (sidebar visible)")
            return
        
        # If we're not on login/auth page and not logged in, something's wrong
        if not self.is_visible(self.USERNAME_INPUT):
            print(f"Not on login page. Checking page...")
            print(f"URL: {self.page.url}")
            # Wait a moment and check again
            time.sleep(2)
            if self.is_visible(self.SIDEBAR):
                print("Sidebar now visible")
                return
            if not self.is_visible(self.USERNAME_INPUT):
                # Take screenshot for debugging
                self.page.screenshot(path="debug_screenshot.png")
                print("Screenshot saved to debug_screenshot.png")
                raise Exception(f"Not on login page and not logged in - URL: {self.page.url}")
        
        print("On login page, filling credentials...")
        # Wait for page to be fully loaded
        try:
            self.wait_for_element(self.USERNAME_INPUT, timeout=10000)
            self.wait_for_element(self.PASSWORD_INPUT, timeout=10000)
            
            # Try to find the login button - might have different selectors
            login_button = None
            for selector in [self.LOGIN_BUTTON, self.LOGIN_BUTTON_ALT, self.LOGIN_BUTTON_ALT2, 'button', 'mwc-button']:
                try:
                    if self.page.is_visible(selector, timeout=2000):
                        login_button = selector
                        print(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                # Try just pressing Enter on the password field as last resort
                print("Could not find login button, will press Enter on password field...")
                login_button = None
                
        except Exception as e:
            print(f"Error waiting for login elements: {e}")
            # Debug: try to find what buttons are available
            buttons = self.page.query_selector_all("button")
            print(f"Found {len(buttons)} buttons on page")
            for i, btn in enumerate(buttons[:5]):  # Show first 5
                try:
                    text = btn.text_content()
                    btn_type = btn.get_attribute("type")
                    print(f"Button {i}: text='{text}', type='{btn_type}'")
                except:
                    pass
            self.page.screenshot(path="debug_login_page.png")
            print("Screenshot saved to debug_login_page.png")
            raise
        
        # Fill credentials
        print("Filling username...")
        self.fill(self.USERNAME_INPUT, username)
        time.sleep(0.3)
        
        print("Filling password...")
        self.fill(self.PASSWORD_INPUT, password)
        
        # Wait a moment for form to be ready and make sure password field has focus
        time.sleep(0.5)
        
        # Ensure password field is focused
        self.page.locator(self.PASSWORD_INPUT).focus()
        time.sleep(0.3)
        
        # Debug screenshot before clicking
        self.page.screenshot(path="before_login_click.png")
        print("Screenshot saved before login button click")
        
        # Submit form with Enter key
        print("Pressing Enter to submit form...")
        self.page.locator(self.PASSWORD_INPUT).press("Enter")
        
        print("Waiting for navigation after login attempt...")
        time.sleep(3)  # Give it time to process
        
        # Wait for either navigation away from login page or error message
        try:
            # Wait for login form to disappear (successful login)
            self.page.wait_for_selector(self.USERNAME_INPUT, state="hidden", timeout=10000)
        except Exception:
            # Check if we're now on the authorize page (login successful, need to authorize)
            if "/auth/authorize" in self.page.url and self.is_visible(self.AUTHORIZE_BUTTON):
                print("Login successful, now on authorize page - clicking authorize...")
                self.click(self.AUTHORIZE_BUTTON)
                time.sleep(3)
                return
            
            # Check if still on login page (login failed)
            if self.is_visible(self.USERNAME_INPUT):
                error_msg = "Login failed - still on login page"
                if self.is_visible(self.ERROR_MESSAGE):
                    error_text = self.get_text(self.ERROR_MESSAGE)
                    error_msg += f": {error_text}"
                self.page.screenshot(path="login_failed.png")
                print(f"Login failed screenshot saved. URL: {self.page.url}")
                raise Exception(error_msg)
        
        # Wait for page to stabilize after login
        time.sleep(2)
    
    def login_with_token(self, token: str):
        """
        Login using a long-lived access token.
        
        Args:
            token: Home Assistant long-lived access token
        """
        # Set auth token in local storage
        self.page.evaluate(f"""
            () => {{
                localStorage.setItem('hassTokens', JSON.stringify({{
                    access_token: '{token}',
                    token_type: 'Bearer'
                }}));
            }}
        """)
        
        # Navigate to home page
        self.navigate_to(self.ha_url)
        time.sleep(2)
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in by looking for main UI elements."""
        # Wait a moment for page to settle
        time.sleep(1)
        # Look for sidebar which appears after login
        return self.is_visible(self.SIDEBAR)
