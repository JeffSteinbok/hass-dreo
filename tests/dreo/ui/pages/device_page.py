"""
Page object for Home Assistant device pages.
Handles interactions with Dreo devices in the Home Assistant UI.
"""
import time
from .base_page import BasePage


class DevicePage(BasePage):
    """Home Assistant device control page object."""
    
    def __init__(self, page, ha_url: str):
        super().__init__(page)
        self.ha_url = ha_url
    
    def navigate_to_device(self, device_name: str):
        """
        Navigate to a specific device by name.
        
        Args:
            device_name: The name of the device to navigate to
        """
        # Navigate to devices page
        self.navigate_to(f"{self.ha_url}/config/devices/dashboard")
        time.sleep(2)
        
        # Search for device
        search_input = 'input[placeholder*="Search"]'
        if self.is_visible(search_input):
            self.fill(search_input, device_name)
            time.sleep(1)
        
        # Click on device card
        device_card = f'text="{device_name}"'
        self.click(device_card)
        time.sleep(1)
    
    def get_entity_state(self, entity_name: str) -> str:
        """
        Get the state of an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            The state value as a string
        """
        # Try to find entity by name and get its state
        entity_selector = f'[data-entity*="{entity_name}"]'
        if self.is_visible(entity_selector):
            return self.get_text(entity_selector)
        return None
    
    def turn_on_device(self, device_name: str):
        """Turn on a device."""
        toggle = f'[data-entity*="{device_name}"] ha-switch'
        if self.is_visible(toggle):
            current_state = self.page.get_attribute(toggle, 'aria-checked')
            if current_state == 'false':
                self.click(toggle)
                time.sleep(1)
    
    def turn_off_device(self, device_name: str):
        """Turn off a device."""
        toggle = f'[data-entity*="{device_name}"] ha-switch'
        if self.is_visible(toggle):
            current_state = self.page.get_attribute(toggle, 'aria-checked')
            if current_state == 'true':
                self.click(toggle)
                time.sleep(1)
    
    def set_fan_speed(self, speed: int):
        """
        Set fan speed using slider or buttons.
        
        Args:
            speed: Speed level (typically 1-4 or 1-9)
        """
        # Look for speed control
        speed_control = '[data-entity*="fan"] input[type="range"]'
        if self.is_visible(speed_control):
            self.page.fill(speed_control, str(speed))
            time.sleep(1)
    
    def set_temperature(self, temperature: int):
        """
        Set target temperature.
        
        Args:
            temperature: Target temperature
        """
        temp_input = 'input[aria-label*="Temperature"]'
        if self.is_visible(temp_input):
            self.fill(temp_input, str(temperature))
            time.sleep(1)
    
    def set_humidity(self, humidity: int):
        """
        Set target humidity.
        
        Args:
            humidity: Target humidity percentage
        """
        humidity_input = 'input[aria-label*="Humidity"]'
        if self.is_visible(humidity_input):
            self.fill(humidity_input, str(humidity))
            time.sleep(1)
    
    def select_mode(self, mode: str):
        """
        Select device mode from dropdown.
        
        Args:
            mode: Mode name (e.g., "Normal", "Auto", "Sleep")
        """
        # Click mode selector
        mode_selector = 'ha-select[label*="Mode"]'
        if self.is_visible(mode_selector):
            self.click(mode_selector)
            time.sleep(0.5)
            
            # Select option
            option = f'mwc-list-item:has-text("{mode}")'
            self.click(option)
            time.sleep(1)
    
    def get_sensor_value(self, sensor_name: str) -> str:
        """
        Get current sensor value.
        
        Args:
            sensor_name: Name of the sensor (e.g., "Temperature", "Humidity")
            
        Returns:
            Sensor value as string
        """
        sensor = f'text="{sensor_name}"'
        if self.is_visible(sensor):
            # Get the value next to the sensor name
            parent = self.page.locator(sensor).locator('..')
            return parent.text_content()
        return None


class DreoFanPage(DevicePage):
    """Page object specific to Dreo fan devices."""
    
    def toggle_oscillation(self):
        """Toggle oscillation on/off."""
        osc_button = 'button:has-text("Oscillation")'
        if self.is_visible(osc_button):
            self.click(osc_button)
            time.sleep(1)
    
    def get_current_speed(self) -> int:
        """Get current fan speed."""
        speed_display = '[data-entity*="fan"] .speed'
        if self.is_visible(speed_display):
            text = self.get_text(speed_display)
            # Extract number from text
            import re
            match = re.search(r'\d+', text)
            if match:
                return int(match.group())
        return 0


class DreoHumidifierPage(DevicePage):
    """Page object specific to Dreo humidifier devices."""
    
    def get_current_humidity(self) -> int:
        """Get current humidity reading."""
        return self.get_sensor_value("Humidity")
    
    def get_target_humidity(self) -> int:
        """Get target humidity setting."""
        return self.get_sensor_value("Target Humidity")
    
    def get_water_level(self) -> str:
        """Get water level status."""
        return self.get_sensor_value("Water Level")


class DreoHeaterPage(DevicePage):
    """Page object specific to Dreo heater devices."""
    
    def get_current_temperature(self) -> float:
        """Get current temperature reading."""
        return self.get_sensor_value("Temperature")
    
    def get_target_temperature(self) -> float:
        """Get target temperature setting."""
        temp_input = 'input[aria-label*="Temperature"]'
        if self.is_visible(temp_input):
            return float(self.page.get_attribute(temp_input, 'value'))
        return None
