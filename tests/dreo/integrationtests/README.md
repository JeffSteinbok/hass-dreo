# Dreo Integration Tests

*This aims to briefly describe how these tests are setup.*

For Unit Tests, see [README.md](../README.md)

- All tests inherit off IntegrationTestBase.py
- All API responses are in the **api_responses** folder.
    - Tests can specify a version of get_devices response for their specific scenarios. 
        - Recommendation would be to have seperate get_devices files for each device to test.
    - Each device initial state is in a JSON file named get_device_state_[sn].json
    - Sensitive information should be redacted.
- Tests can/should call the setters to change device settings and inspect the parameters sent on the websocket.

Please feel free to contribute more tests for various device types.