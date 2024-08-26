#from custom_components.dreo.pydreo import PyDreo
import sys
import importlib.util
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.dreo.pydreo import * # pylint: disable=W0401,W0614
else:
    spec = importlib.util.spec_from_file_location("pydreo", "custom_components/dreo/pydreo/__init__.py")
    pydreo = importlib.util.module_from_spec(spec)
    sys.modules["pydreo"] = pydreo
    spec.loader.exec_module(pydreo)
    from pydreo import * # pylint: disable=W0401,W0614
