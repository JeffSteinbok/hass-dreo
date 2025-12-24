"""
Base configuration loader for UI tests.
"""
import os
import sys
from pathlib import Path

# Add config directory to path
config_dir = Path(__file__).parent
sys.path.insert(0, str(config_dir))

# Import constants (always available)
from constants import DEFAULT_TIMEOUT, ACTION_TIMEOUT

# Import model mappings (always available)
from models import MODEL_DEVICES, CONFIGURED_MODELS

# Import auth config
try:
    from test_config import *  # pylint: disable=wildcard-import,unused-wildcard-import
except ImportError:
    print("WARNING: test_config.py not found. Using example configuration.")
    print("Copy config/test_config.example.py to config/test_config.py and configure it.")
    from test_config_example import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Allow environment variable overrides
HA_URL = os.getenv("HA_URL", HA_URL)
HA_USERNAME = os.getenv("HA_USERNAME", HA_USERNAME)
HA_PASSWORD = os.getenv("HA_PASSWORD", HA_PASSWORD)
HA_ACCESS_TOKEN = os.getenv("HA_ACCESS_TOKEN", HA_ACCESS_TOKEN)
