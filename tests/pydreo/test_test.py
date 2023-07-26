#from custom_components.dreo.pydreo import PyDreo

import time
import sys
import importlib.util
import sys


from typing import Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.dreo.pydreo import PyDreo, PyDreoBaseDevice
else:
    spec = importlib.util.spec_from_file_location("pydreo", "custom_components/dreo/pydreo/__init__.py")
    pydreo = importlib.util.module_from_spec(spec)
    sys.modules["pydreo"] = pydreo
    spec.loader.exec_module(pydreo)
    from pydreo import PyDreo, PyDreoBaseDevice

def test_test():
    assert True

def test_test2():
    x = PyDreo("a", "b")
    x.login()