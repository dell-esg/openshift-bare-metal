#!/bin/bash

BOOTSTRAP_CONFIG="[connection]
type=ethernet
interface-name=ens3
[ethernet]
[ipv4]
method=manual
addresses=${2}
gateway=${3}
dns=${4}"

cat <<_EOF_ > $1/bootstrap_network_config.ign
{
  "path": "/etc/NetworkManager/system-connections/ens3.nmconnection",
  "mode": 384,
  "contents": {
    "source": "data:text/plain;charset=utf-8;base64,$(echo "${BOOTSTRAP_CONFIG}" | base64 -w 0)"
  }
}
_EOF_

sudo mv $1/bootstrap.ign $1/bootstrap.ign.orig

sudo jq '.storage.files += $input' $1/bootstrap.ign.orig --slurpfile input $1/bootstrap_network_config.ign > $1/bootstrap.ign
