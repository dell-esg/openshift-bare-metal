## Execute Playbook by following steps as below

- Follow Chapter 3 Setup CSAH node in OCP 42 Dell Deployment Guide < Refer to Guide location > to run ansible playbook

- Gather the IP address and NIC mac address of bootstrap, master(s), worker(s) nodes 

- Update the hosts file located in repository home directory

- Current hosts file already is filled with sample values and comments are included for each section accordingly.

- Below are the links to the OpenShift software files. Download them and specify the names accordingly for each variable in hosts file. These files are also referenced in Deployment Guide.

  a) [uefi_file](https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/4.2.0/rhcos-4.2.0-x86_64-metal-uefi.raw.gz)

  b) [initramfs](https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/4.2.0/rhcos-4.2.0-x86_64-installer-initramfs.img)

  c) [openshift_client](https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux-4.2.0.tar.gz)

  d) [openshift_installer](https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-install-linux-4.2.0.tar.gz)

  e) [kernel_file](https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/4.2.0/rhcos-4.2.0-x86_64-installer-kernel)

  f) [pull_secret_file](https://cloud.redhat.com/openshift/install/metal/user-provisioned)
