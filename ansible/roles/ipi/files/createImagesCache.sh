#!/bin/bash

#Download the installer
VERSION=$1
RELEASE_IMAGE=$(curl -s https://mirror.openshift.com/pub/openshift-v4/clients/ocp/$VERSION/release.txt | grep 'Pull From: quay.io' | awk -F ' ' '{print $3}')
cmd=openshift-baremetal-install
pullsecret_file=$2
extract_dir=/home/kni

#Download the oc binary and openshift-baremetal-install programs:
sudo curl -s https://mirror.openshift.com/pub/openshift-v4/clients/ocp/$VERSION/openshift-client-linux.tar.gz | sudo tar zxvf - -C /usr/local/bin oc
if [ $? -ne 0 ]; then
  echo "Error: Failed to download oc client"
  exit $?
fi
#sudo cp oc /usr/local/bin
sudo /usr/local/bin/oc adm release extract --registry-config "${pullsecret_file}" --command=$cmd --to "${extract_dir}" ${RELEASE_IMAGE} && sudo cp "${extract_dir}"/openshift-baremetal-install /usr/local/bin
if [ $? -ne 0 ]; then
  echo "Error: Failed to extract openshift-baremetal-install"
  exit $?
fi
#sudo cp "${extract_dir}"/openshift-baremetal-install /usr/local/bin

#Open firewall port 8080 to be used for RHCOS image caching
sudo firewall-cmd --add-port=8080/tcp --zone=public --permanent
sudo firewall-cmd --reload

#Create a directory to store the bootstraposimage:
mkdir /home/kni/rhcos_image_cache

#Set the appropriate SELinux context for the newly created directory:
sudo semanage fcontext -a -t httpd_sys_content_t "/home/kni/rhcos_image_cache(/.*)?"
sudo restorecon -Rv /home/kni/rhcos_image_cache/

#Get the URI for the RHCOS image that the installation program will deploy on the bootstrap VM:
RHCOS_QEMU_URI=$(/usr/local/bin/openshift-baremetal-install coreos print-stream-json | jq -r --arg ARCH "$(arch)" '.architectures[$ARCH].artifacts.qemu.formats["qcow2.gz"].disk.location')
RHCOS_QEMU_NAME=${RHCOS_QEMU_URI##*/}
RHCOS_QEMU_UNCOMPRESSED_SHA256=$(/usr/local/bin/openshift-baremetal-install coreos print-stream-json | jq -r --arg ARCH "$(arch)" '.architectures[$ARCH].artifacts.qemu.formats["qcow2.gz"].disk["uncompressed-sha256"]')

#Download the image and place it in the /home/kni/rhcos_image_cache directory:
curl -L ${RHCOS_QEMU_URI} -o /home/kni/rhcos_image_cache/${RHCOS_QEMU_NAME}
if [ $? -ne 0 ]; then
  echo "Error: Failed to download RHCOS image"
  exit $?
fi

#Confirm SELinux type is of httpd_sys_content_t for the new file:
#ls -Z /home/kni/rhcos_image_cache

#Create the pod:
sudo podman run -d --name rhcos_image_cache -v /home/kni/rhcos_image_cache:/var/www/html -p 8080:8080/tcp quay.io/centos7/httpd-24-centos7:latest
if [ $? -ne 0 ]; then
  echo "Error: Failed to create httpd pod"
  exit $?
fi

#Generate the bootstrapOSImage configuration:
BAREMETAL_IP=$(ip addr show dev baremetal | awk '/inet /{print $2}' | cut -d"/" -f1)
BOOTSTRAP_OS_IMAGE="http://${BAREMETAL_IP}:8080/${RHCOS_QEMU_NAME}?sha256=${RHCOS_QEMU_UNCOMPRESSED_SHA256}"
echo "    bootstrapOSImage=${BOOTSTRAP_OS_IMAGE}"
