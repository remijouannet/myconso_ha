# myconso_ha


# myconso_ha Home Assistant Integration

Provides last index for very counter of your housings behind the [Myconso application](https://play.google.com/store/apps/details?id=fr.proxiserve.myconso&hl=fr)

## Installation

Easiest install is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=remijouannet&repository=myconso_ha&category=integration)

`HACS -> Integrations -> Explore & Add Repositories -> myconso_ha`

### Development

Edit the code
```
mkdir -p config
cp configuration.yaml config/
#container is for macos, docker should also work
container run -i --name ha -v $(pwd)/config:/config -v $(pwd)/custom_components:/config/custom_components -e TZ=MY_TIME_ZONE -p 8123:8123 ghcr.io/home-assistant/home-assistant:stable && container rm ha
```

Access the local home assistant on http://localhost:8123

