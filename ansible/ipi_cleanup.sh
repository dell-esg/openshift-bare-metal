#!/bin/bash

killall -u kni
userdel -r kni
rm -rf /home/kni/
rm -rf /usr/local/bin/oc
semanage fcontext -d -t httpd_sys_content_t "/home/kni/rhcos_image_cache(/.*)?"

sudo virsh pool-destroy default
sudo virsh pool-undefine default

#sudo nmcli connection delete bridge-slave
#sudo nmcli connection delete baremetal

sudo podman stop -a
sudo podman rm -a

for i in $(sudo virsh list | tail -n +3 | grep bootstrap | awk {'print $2'}); do sudo virsh destroy $i; sudo virsh undefine $i; sudo virsh vol-delete $i --pool $i; sudo virsh vol-delete $i.ign --pool $i; sudo virsh pool-destroy $i; sudo virsh pool-undefine $i; done

#systemctl stop httpd
