# Dreo Space Heaters

Heaters are modeled as climate devices in Home Assistant, which enables the ability to put a thermostat control for the heater into your HA dashboards. Some examples are shown below.

## Important Notes

### Oscillation Support

Oscillation is supported, but shown under "swing mode" since this is how Home Assistant's climate device models that feature.

### Tower Fan & Heater Combos

The Tower Fan & Heater 706S (DR-HSH016S) is a heater and a 12-speed tower fan in one unit, so its climate entity carries a few extra controls:

- **HVAC mode** `heat` is the HEAT function (Power Heat with presets `H1`–`H5`, or `eco` with the thermostat); `fan_only` is the FAN function.
- **Fan mode** is the fan speed (`1`–`12`) of the FAN function. A speed set while heating or off is stored by the unit but only takes effect once it is in `fan_only`; changing the speed never powers the unit on (use `fan_only` or a fan preset for that).
- **Target temperature** is honoured by the unit in `eco` only (on or off), as on the other heaters; in Power Heat it is ignored.
- **Preset modes** `Natural`, `Sleep` and `Auto` are the FAN function's modes; selecting one switches the unit to the FAN function, just as the `H1`–`H5` presets switch it to HEAT. `none` is the plain fixed-speed fan mode and only applies while in the FAN function.
- **Swing mode** selects a symmetric oscillation arc (`30°`–`120°`) or `off`. Asymmetric arcs set in the Dreo app are shown as the nearest arc, and can be set exactly with the *Horizontal Oscillation Angle Left/Right* numbers; *Horizontal Angle* points the unit while it is not oscillating.
- A *Display Mode* select (off / on / auto-brightness) and a *Window Detection* switch are created alongside the usual child lock and panel sound switches.

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
