# Deploying Red Hat OpenShift® Container Platform 3.10 with OpenShift Container Storage

## Instructions
Please refer to the [Reference Architecture document](https://tbd.pdf) for network diagrams and detailed server information.

Though some of these commands can be run as a non-root user, it is assumed they are being run as root unless stated otherwise.

### Clone the repository
```bash
$ git clone https://github.com/dell/openshift-container-architecture.git
```

### Populating the inventory file
The inventory file has to be filled manually.
Refer to `hosts.fv4` for possible variables.

```bash
$ cd openshift-container-architecture
$ cp hosts.fv4 /etc/ansible/hosts
$ vim /etc/ansible/hosts
```

### Switch Configuration
The dellos10 configuration role requires Ansible v2.5, which we will use via a container.
As indicated in the RA whitepaper, connect one of the 1Gb LOM ports in the bastion node to VLAN 7 in the S3048-ON switch (which also has the S5048F-ON management ports connected to it) so you can connect and manage the S5048F-ON switches via Ansible. 

In the bastion node, build the container image (install the docker engine if not already installed). Run as root:

```bash
$ cd src/os10-configuration
$ docker build -t ansible25 .
```

Then, update the inventory group `[dellos10]` with your IP addresses and credentials and copy to the current directory (since we will volume-mount the current directory inside the container). Run as root:

```bash
$ cd src/os10-configuration
$ vim /etc/ansible/hosts                      # update as needed
$ cp /etc/ansible/hosts .                     # copy to current directory
$ vim vars/all.yaml                           # update as needed
$ chcon -Rt container_file_t .                # fix SELinux context so we can mount in container
$ docker run --rm -it -v $PWD:/playbooks ansible25 -i hosts configure_dellos10.yaml
PLAY [dellos10] ******************************************************************************************

TASK [networking_setup : Configuring top level settings] *************************************************
changed: [dellos10_sw1]
changed: [dellos10_sw2]

TASK [networking_setup : Applying stp configuration] *****************************************************
changed: [dellos10_sw1]
changed: [dellos10_sw2]

TASK [networking_setup : Applying vlt configuration] *****************************************************
changed: [dellos10_sw2]
changed: [dellos10_sw1]

TASK [networking_setup : Applying vlans configuration] ***************************************************
changed: [dellos10_sw1]
changed: [dellos10_sw2]

TASK [networking_setup : Applying interfaces configuration] **********************************************
changed: [dellos10_sw1]
changed: [dellos10_sw2]

PLAY RECAP ***********************************************************************************************
dellos10_sw1               : ok=5    changed=5    unreachable=0    failed=0
dellos10_sw2               : ok=5    changed=5    unreachable=0    failed=0
```

### Server BIOS configuration
Some settings in the BIOS need to be updated in all the servers, like enabling PxE booting from the correct NIC and setting up the right boot order.
A [Server Configuration Profile (SCP)](https://dell.to/2NpRJ9a) can be imported via the Integrated Dell Remote Management Controller (iDRAC) to achieve this in an automated way.
The Dell OpenManage Ansible modules and required libraries need to be installed.

In the bastion node, run as root:

```bash
$ subscription-manager repos --enable=rhel-server-rhscl-7-rpms   # enable Software Collections repo
$ yum -y install python27-python-pip -y                          # install pip
$ scl enable python27 bash                                       # setup pip from RHSCL
$ pip install omsdk                                              # install OpenManage SDK
$ git clone https://github.com/dell/Dell-EMC-Ansible-Modules-for-iDRAC.git
$ cd Dell-EMC-Ansible-Modules-for-iDRAC
$ python install.py                                              # install Ansible modules
```

After the Ansible modules have been installed, an NFS share has to be created in the bastion node where the SCP files will be placed so that they can be later imported.

```bash
$ export PYTHONPATH=/opt/rh/python27/root/usr/lib/python2.7/site-packages   # may want to put in .bashrc
$ cd src/bios-configuration
$ vim /etc/ansible/hosts                                                    # update as needed
$ vim vars/all.yaml                                                         # update as needed
$ ansible-playbook setup_SCP_share.yaml
```

Now that the NFS share is ready and we have placed the SCP files, we can import them into the iDRACs and apply the BIOS settings we need:

```bash
$ ansible-playbook configure_bios.yaml
```

This will:

- Enable IPMI
- Enable PxE for addon 25Gb NIC port 1
- Disable PxE for embedded NIC port 1
- Setup boot order: 1) BOSS card 2) 25Gb NIC port 1

**Please note that this will cause the servers to reboot so the new BIOS settings can take effect.**

### Power Management

We have provided playbooks to manage power in your servers.
Before running any of these playooks, be sure `PYTHONPATH` is defined:

```
$ export PYTHONPATH=/opt/rh/python27/root/usr/lib/python2.7/site-packages   # may want to put in .bashrc
```

To do a one-time PxE boot:
```bash
$ ansible-playbook one_time_boot_nic.yaml
```

To reboot:

```bash
$ cd src/power-management
$ ansible-playbook reboot_servers.yml
```

To power off:
```bash
$ ansible-playbook power_off_servers.yml
```

To power on:
```bash
$ ansible-playbook power_on_servers.yml
```

### Provisioning system setup

```bash
$ ansible-playbook ipxe-deployer/ipxe.yml
$ env IPMI_PASSWORD=password /tftp/reboot.sh -b pxe -r -f /tftp/ipmi.list.txt
```

### Preparing the nodes for OpenShift Container Platform

```bash
$ ansible-playbook src/prerequisites/nodes_setup.yaml -k
```

### Setting up multimaster HA
switch user to *openshift* and then run:

```bash
$ su - openshift
$ ansible-playbook src/keepalived-multimaster/keepalived.yaml
```

### Deploying OpenShift cluster
As user *openshift* run:

```bash
$ ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/byo/config.yml
```
