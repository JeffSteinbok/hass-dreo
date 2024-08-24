"""PyDreo Test Defaults"""
from typing import TYPE_CHECKING
from requests.structures import CaseInsensitiveDict

if TYPE_CHECKING:
    from .imports import * # pylint: disable=W0401,W0614
else:
    from imports import * # pylint: disable=W0401,W0614

class Defaults:
    """General defaults for API responses and requests.

    Attributes
    ----------
    token : str
        Default token for API requests
    active_time : str
        Default active time for API responses
    account_id : str
        Default account ID for API responses
    active_time : str
        Default active time for API responses
    color: Color (dataclass)
        Red=50, Green=100, Blue=225, Hue=223, Saturation=77.78, value=88.24
        Default Color dataclass
        contains red, green, blue, hue, saturation and value attributes

    Methods
    --------
    name(dev_type='NA')
        Default device name created from "dev_type-NAME"
    cid(dev_type='NA')
        Default device cid created from "dev_type-CID"
    uuid(dev_type='NA')
        Default device uuid created from "dev_type-UUID"
    macid(dev_type='NA')
        Default device macid created from "dev_type-MACID"
    """

    token = 'sample_tk'
    account_id = 'sample_id'
    trace_id = "TRACE_ID"
    active_time = 1
    brightness = 100
    color_temp = 100
    bool_toggle = True
    str_toggle = 'on'
    bin_toggle = 1

    @staticmethod
    def name(dev_type: str = 'NA'):
        """Name of device with format f"{dev_type}-NAME".

        Parameters
        ----------
        dev_type : str
            Device type use to create default name

        Returns
        -------
        str
            Default name for device f"dev_type-NAME"
        """
        return f'{dev_type}-NAME'

    @staticmethod
    def cid(dev_type='NA'):
        """CID for a device with format f"{dev_type}-CID".

        Parameters
        ----------
        dev_type : str
            Device type use to create default cid

        Returns
        -------
        str
            Default cid for device f"dev_type-CID"
        """
        return f'{dev_type}-CID'

    @staticmethod
    def uuid(dev_type='NA'):
        """UUID for a device with format f"{dev_type}-UUID".

        Parameters
        ----------
        dev_type : str
            Device type use to create default UUID

        Returns
        -------
        str
            Default uuid for device f"{dev_type}-UUID"
        """
        return f'{dev_type}-UUID'

    @staticmethod
    def macid(dev_type='NA'):
        """MACID for a device with format f"{dev_type}-MACID".

        Parameters
        ----------
        dev_type : str
            Device type use to create default macid

        Returns
        -------
        str
            Default macID for device f"{dev_type}-MACID"
        """
        return f'{dev_type}-MACID'


API_DEFAULTS = CaseInsensitiveDict({
    'accountID': Defaults.account_id,
    'token': Defaults.token,
    "tk": Defaults.token,
    "traceId": "TRACE_ID",
    'verifyEmail': 'EMAIL',
    'nickName': 'NICKNAME',
    'password': 'PASSWORD',
    'username': 'EMAIL',
    'email': 'EMAIL',
    'deviceName': 'NAME'

})
