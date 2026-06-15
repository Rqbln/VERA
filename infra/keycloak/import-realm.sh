#!/bin/sh
set -e
/opt/keycloak/bin/kc.sh import --file /opt/keycloak/data/import/raip-realm.json --override true
