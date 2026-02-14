# myconso_ha

container run -i --name ha -v $(pwd)/config:/config -v $(pwd)/custom_components:/config/custom_components -e TZ=MY_TIME_ZONE -p 8123:8123 ghcr.io/home-assistant/home-assistant:stable && container rm ha


