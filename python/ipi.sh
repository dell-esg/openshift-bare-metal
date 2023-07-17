#! /bin/bash

echo "Setting up kni user."

useradd kni
#echo -n "Enter the password for kni user : "
#read pass
passwd kni

echo "kni ALL=(root) NOPASSWD:ALL" | tee -a /etc/sudoers.d/kni
chmod 0400 /etc/sudoers.d/kni
su - kni -c "ssh-keygen -t ed25519 -f /home/kni/.ssh/id_rsa -N ''"
dnf install -y libvirt qemu-kvm mkisofs python3-devel jq ipmitool
usermod --append --groups libvirt kni
systemctl start firewalld
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --reload


systemctl enable libvertd --now
virsh pool-define-as --name default --type dir --target /var/lib/libvirt/images
virsh pool-start default
virsh pool-autostart default

echo "Place the pull-secret.txt file under /home/kni"
