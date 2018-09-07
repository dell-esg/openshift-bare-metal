# Deploying Red Hat OpenShift® Container Platform 3.10 with Container-Native Storage

## Instructions
Please refer to [Reference Architecture document](https://tbd.pdf) for detailed instructions.

### Clone the repository
`$ git clone https://github.com/dell/openshift-container-architecture.git`

### Populating inventory file
The inventory file has to be filled manually.
Refer to *hosts.fv4* for possible variables.

```
# cp hosts.fv4 /etc/ansible/hosts
# vim /etc/ansible/hosts
```

### Switch Configuration
The Dell OS10 configuration role requires Ansible v2.5, which we will use via a Docker container. In the bastion node, build the container image (install Docker if not already installed). Run as root:

```
# cd src/os10-configuration
# docker build -t ansible25 .
```

Then, update the dellos10 section in the inventory file with your IP addresses and credentials and copy to the current directory (since we are volume-mounting the current directory inside the container). Run as root:

```
$ cd src/os10-configuration
$ vi ../../hosts.fv4			# update as needed
$ cp ../../hosts.fv4 .			# copy to current directory (to be mounted)
$ chcon -Rt container_file_t .		# fix SELinux context so we can mount inside container
$ docker run --rm -it -v $PWD:/playbooks ansible25 -i hosts.fv4 configure_dellos10.yaml`
```

### Server BIOS configuration
Some settings in the BIOS need to be updated, like enabling PXE booting from the correct NIC and setting up the right boot order. A [Server Configuration Profile (SCP)](https://dell.to/2NpRJ9a) can be imported via the Integrated Dell Remote Management Controller (iDRAC) to achieve this in an automated way. The Dell OpenManage Ansible modules and required libraries need to be insallted. 

In the bastion node, run as root:

```
# subscription-manager repos --enable rhel-server-rhscl-7-rpms   # enable Software Collections repo
# yum -y install python27-python-pip -y                          # install pip
# scl enable python27 bash                                       # setup pip from RHSCL
# pip install omsdk                                              # install OpenManage SDK library
# git clone https://github.com/dell/Dell-EMC-Ansible-Modules-for-iDRAC.git
# cd Dell-EMC-Ansible-Modules-for-iDRAC
# python install.py                                              # install Ansible modules we'll use
```

After the Ansible modules have been installed, an NFS share has to be created where the required SCP files will be placed so that they be imported by iDRAC. Update *src/bios=configuration/inventory.yaml* and *src/bios-configuration/vars/all.yaml*, though if you are using the same set of IP addresses recommended in this Reference Architecture then you can leave them as-is.

```
$ export PYTHONPATH=/opt/rh/python27/root/usr/lib/python2.7/site-packages    # may want to put in .bashrc
$ cd src/bios-configuration
$ ansible-playbook -i inventory.yaml setup_SCP_share.yaml
```

Now that the NFS share is ready and we have placed the SCP files, we can import them into the iDRACs and apply the BIOS settings we need:

```
$ ansible-playbook -i inventory.yaml configure_bios.yaml
```

This will:

- Enable IPMI
- Disable PXE for embedded NIC port 1
- Enable PXE for addon NIC port 1
- Setup boot order: 1) BOSS cards 2) NIC

Please note that this will cause the servers to reboot.

Once you are ready to provision the OS, you can do a one time PXE bootb:

`$ ansible-playbook -i inventory.yaml one_time_boot_nic.yaml`

### Provisioning system setup

```
$ ansible-playbook ipxe-deployer/ipxe.yml
$ env IPMI_PASSWORD=password /tftp/reboot.sh -b pxe -r -f /tftp/ipmi.list.txt
```

### Preparing the nodes for OpenShift Container Platform

`$ ansible-playbook src/prerequisites/nodes_setup.yaml -k`

### Setting up multimaster HA
switch user to *openshift* and then run:

```
# su - openshift
$ ansible-playbook src/keepalived-multimaster/keepalived.yaml
```

### Deploying OpenShift cluster
As user *openshift* run:

`$ ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/byo/config.yml`
