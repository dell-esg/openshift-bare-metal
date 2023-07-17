#!/bin/bash

sudo virsh destroy bootstrapkvm
sudo virsh undefine --nvram bootstrapkvm
rm -rf /home/bootstrapvm-disk.qcow2


userdel	-r core
rm -rf /home/core/

rm -rf /var/www/

systemctl stop named
systemctl stop dhcpd
rm -f /etc/dhcp/dhcpd.conf
rm -rf /var/named/
yum remove -y bind openshift-clients dhcp-server keepalived
ssh csah-sec "yum remove -y bind openshift-clients dhcp-server keepalived"
