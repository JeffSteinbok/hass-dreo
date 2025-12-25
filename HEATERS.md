# Dreo Space Heaters

Heaters are modeled as climate devices in Home Assistant, which enables the ability to put a thermostat control for the heater into your HA dashboards. Some examples are shown below.

## Important Notes

### Oscillation Support

Oscillation is supported, but shown under "swing mode" since this is how Home Assistant's climate device models that feature.

### Remote Control Timeout

**Important:** To satisfy UL safety listings, the remote control is disabled if it has not been used for 24 hours. If you find the heater is not responding to commands, you will need to give a quick tap on the WiFi button on the physical heater to resume the ability to control the device remotely via either the Dreo app or this Home Assistant integration.

## Dashboard Examples

### Thermostat Modes

<table>
    <tr>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/auto-mode-thermostat.png" width="300" alt="eco/auto mode thermostat"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/heat-mode-thermostat.png" width="300" alt="heat mode thermostat"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/fan-mode-thermostat.png" width="300" alt="fan mode thermostat"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/off-mode-thermostat.png" width="300" alt="off mode thermostat"></td>
    </tr>
    <tr>
        <td>Auto/Eco Mode</td>
        <td>Heat Mode</td>
        <td>Fan Mode</td>
        <td>Off</td>
    </tr>
</table>

### Control Options

<table>
    <tr>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/mode-list.png" width="200" alt="HVAC mode list"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/fan-mode-list.png" width="200" alt="fan mode list"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/preset-mode-list.png" width="200" alt="preset mode list"></td>
        <td><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/swing-mode-list.png" width="200" alt="swing mode list"></td>
    </tr>
    <tr>
        <td>HVAC Modes</td>
        <td>Fan Modes</td>
        <td>Preset Modes</td>
        <td>Swing Modes</td>
    </tr>
</table>

### Entity Views

<table>
    <tr>
        <td align="center"><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/heater-entities.png" width="200" alt="heater entities"></td>
        <td align="center"><img src="https://raw.githubusercontent.com/jeffsteinbok/hass-dreo/main/images/compact-thermostat.png" width="200" alt="compact-thermostat"></td> 
    </tr>
    <tr>
        <td align="center">Heater Entities</td>
        <td align="center">Compact Thermostat View</td>
    </tr>
</table>

## Supported Models

See the [Supported Models](SUPPORTED_MODELS.md#space-heaters) page for a complete list of tested heater models.
