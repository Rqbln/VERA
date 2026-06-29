#!/bin/sh
set -e
/opt/keycloak/bin/kc.sh import --file /opt/keycloak/data/import/vera-realm.json --override true
