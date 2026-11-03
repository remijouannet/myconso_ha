# myconso_ha Home Assistant Integration

Provides index for every counter of your housings behind the [Myconso application](https://play.google.com/store/apps/details?id=fr.proxiserve.myconso&hl=fr)

## Installation

Easiest install is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=remijouannet&repository=myconso_ha&category=integration)

`HACS -> Integrations -> Explore & Add Repositories -> myconso_ha`

Restart Home Assistant, then add the integration from `Settings -> Devices & services -> Add integration -> myconso`.
The setup asks for your MyConso email and password (only the resulting tokens are stored).

## Sensors

Each account can have multiple housing. Each housing is a device with one sensor per counter per location, showing its latest index:

| Counter | `fluidtype` | Device class | Unit |
|---------|-------------|--------------|------|
| `Heating <Location>` | `heating` | energy | kWh |
| `Climatisation <Location>` | `clim` | energy | kWh |
| `Hot water <Location>` | `waterHot` | water | m³ |
| `Cold water <Location>` | `waterCold` | water | m³ |

Each sensor has these attributes:

| Attribute | Description |
|-----------|-------------|
| `counter` | Counter id |
| `location` | Counter location in the housing |
| `fluidtype` | MyConso fluid type |

Sensors are `total_increasing`.
Data is refreshed every 2 hours.

## Reauthentication

When MyConso rejects the stored tokens, Home Assistant asks you to reauthenticate under `Settings -> Devices & services`: click **Reconfigure** and enter your MyConso email and password again.

### Development

Edit the code
```
mkdir -p config
cp configuration.yaml config/
#container is for macos, docker should also work
container run -i --name ha -v $(pwd)/config:/config -v $(pwd)/custom_components:/config/custom_components -e TZ=MY_TIME_ZONE -p 8123:8123 homeassistant/home-assistant:stable
container rm ha
```

Access the local home assistant on http://localhost:8123
