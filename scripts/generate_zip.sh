#!/bin/bash

cd custom_components/myconso_ha/
zip ../../myconso_ha.zip ./* ./*/* -x '.*' -x '__pycache__/' -x '__pycache__/*'
