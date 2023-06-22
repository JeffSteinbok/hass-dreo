# Dreo Fan for Home Assistant

## Installation

Currently supported fans:
- DR-HTF001S
- DR-HTF008S

### configuration.yaml

```
fan:
    - platform: dreo

dreo:
  username:[email]
  password: [password]
    
logger:
    logs:
        dreo: info
        pydreo: info
```
