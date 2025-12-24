"""
Dreo device model to Home Assistant device name mapping.

This file maps Dreo device models (from e2e test data) to device names in your
Home Assistant instance. Only configure the models you actually have for testing.

Set device name to None for models you don't have - tests will be automatically skipped.
"""

# Device model to device name mapping
# Map each Dreo model (from e2e test data) to the actual device name in your Home Assistant
# Only configure the models you have for testing
MODEL_DEVICES = {
    # Tower Fans
    "HAF001S": "DEBUGTEST - Tower Fan - DR-HTF001S",  # Dreo Cruiser Pro T1 (DR-HTF001S)
    "HAF004S": "DEBUGTEST - Tower Fan - DR-HTF004S",  # Dreo Cruiser Pro T2 (DR-HTF004S)
    "HTF005S": "DEBUGTEST - Tower Fan - DR-HTF005S",  # Tower Fan
    "HTF008S": "DEBUGTEST - Tower Fan - DR-HTF008S",  # Tower Fan
    "HTF010S": "DEBUGTEST - Tower Fan - DR-HTF010S",  # Tower Fan
    
    # Pedestal Fans
    "HPF007S": "DEBUGTEST - Pedestal Fan - DR-HPF007S",  # Pedestal Fan
    "HPF008S": "DEBUGTEST - Pedestal Fan - DR-HPF008S",  # Pedestal Fan
    
    # Ceiling Fans
    "HCF001S": "DEBUGTEST - Ceiling Fan - DR-HCF001S",  # Ceiling Fan
    
    # Humidifiers
    "HHM001S": "DEBUGTEST - Humidifier - DR-HHM001S",  # Dreo Humidifier (DR-HHM001S)
    "HHM014S": "DEBUGTEST - Humidifier - DR-HHM014S",  # Dreo Humidifier (DR-HHM014S/HM774S)
    
    # Heaters
    "HSH003S": "DEBUGTEST - Space Heater - DR-HSH003S",  # Space Heater
    "HSH009S": "DEBUGTEST - Space Heater - DR-HSH009S",  # Space Heater
    "HSH034S": "DEBUGTEST - Space Heater - DR-HSH034S",  # Space Heater
    "WH714S": "DEBUGTEST - Oil Radiator Heater - DR-HSH010S",   # Oil Radiator Heater (DR-HSH010S/OH310)
    
    # Air Conditioners
    "HAC001S": "DEBUGTEST - Portable AC - DR-HAC001S",  # Portable AC
    "HAC006S": "DEBUGTEST - Portable AC - DR-HAC006S",  # Portable AC
    
    # Dehumidifiers
    "HDH002S": "DEBUGTEST - Dehumidifier - DR-HDH002S",  # Dehumidifier
    
    # Air Circulators
    "HEC002S": "DEBUGTEST - Air Circulator - DR-HEC002S",  # Air Circulator
    
    # Chef Maker
    "KCM001S": "DEBUGTEST - Chef Maker - DR-KCM001S",  # Chef Maker
}

# Filter out models that are not configured (None values)
# This is used internally - don't modify
CONFIGURED_MODELS = {k: v for k, v in MODEL_DEVICES.items() if v is not None}
