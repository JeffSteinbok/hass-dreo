# Contributing or Developing this Plugin

This section is very much a work in progress.

# Tests
There are three buckets of tests, please feel free to add as appropriate.
* [PyDreo Unit Tests](tests/pydreo/README.md)
    * These tests ensure that the PyDreo library can parse the JSONs correctly for each device we support.
* [Dreo Unit Tests](tests/dreo/README.md) - That do not talk to PyDreo
    * These tests ensure that the Dreo HA code correctly talks to PyDreo.  For these we mock PyDreo.
* [Dreo Integration Tests](tests/dreo/integrationtests/README.md) - That do talk to PyDreo
    * These integration tests ensure that the Dreo HA code gets what we expect from the device JSON files.

## Getting Network Traces from Dreo App
As of a recent release, Dreo seems to have removed certificate pinning, at least for iOS. That makes all this a bunch easier.

### Setup Fiddler Classic as a Proxy
1. Use Fiddler Classic (http://www.fiddlertool.com) to get a network trace to see what the Dreo app is doing. I won't document here how to setup Fiddler as a proxy or do SSL decryption; Fiddler documentation is pretty good.

