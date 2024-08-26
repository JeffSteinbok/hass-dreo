# PyDreo Unit Tests

*This aims to briefly describe how these unit-tests are setup. Note that this is my first attempt at Python UnitTesting, so there is likely a much better way to do some of this. If you have suggestions, let me know.*

- All tests inherit off TestBase.py
- Imports in each file are done twice, once for PyLint and once for actual test execution.
- All API responses are in the **api_responses** folder.
    - Tests can specify a version of get_devices response for their specific scenarios. 
        - Recommendation would be to have seperate get_devices files for each device to test.
    - Each device initial state is in a JSON file named get_device_state_[sn].json
    - Sensitive information should be redacted.
- Tests can/should call the setters to change device settings and inspect the parameters sent on the websocket.

Please feel free to contribute more tests for various device types.

Note that HomeAssistant tests are not yet done.