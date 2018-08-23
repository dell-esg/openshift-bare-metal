# Deploying Red Hat OpenShift® Container Platform 3.10 with Container-Native Storage

## Instructions
Please, refer to [Reference Architecture document](https://tbd.pdf) for detailed instructions.

### Clone the repository
`git clone git@github.com:dell/openshift-container-architecture.git`

### Creating inventory
The inventory file has to be filled manually.
Refer to *hosts.example* for possible variables.

`cp hosts.example /etc/ansible/hosts;
vim /etc/ansible/hosts`

### Switch Configuration
The OS10 configuration role requires Ansible v2.5, which is available in a container. Build the container image:

`cd src/os10-configuration; docker build -t ansible25 .`

Update inventory.yaml and run:

`docker run --rm -it -v $PWD:/playbooks ansible25 configure_dellos10.yaml`

### Server BIOS Configuration
First, setup NFS share for Server Configuration Profile (SCP) environment that will be used to set BIOS settings on servers. Update inventory_scp_setup.yaml and run:

`ansible-playbook -i src/scp_configuration/inventory_scp_setup.yaml src/scp_configuration/setup_scp_environment.yaml`

Next, update inventory_scp_apply.yaml and run:

`ansible-playbook -i src/scp_configuration/inventory_scp_apply.yaml src/scp_configuration/bios_settings.yaml`

This will:

- Enable IPMI
- Disable PXE for embedded NIC port 1
- Enable PXE for addon NIC port 1
- Setup boot order: 1) BOSS cards 2) NIC

To setup one time boot from NIC, run:

`ansible-playbook -i src/scp_configuration/inventory_scp_apply.yaml src/scp_configuration/one_time_boot.yaml`

### Provisioning system setup

`ansible-playbook ipxe-deployer/ipxe.yml`

`env IPMI_PASSWORD=password /tftp/reboot.sh -b pxe -r -f /tftp/ipmi.list.txt`

### Preparing the nodes for OpenShift Container Platform

`ansible-playbook src/prerequisites/nodes_setup.yaml -k`

### Setting up multimaster HA
switch user to *openshift*:

`su - openshift`

run:

`ansible-playbook src/keepalived-multimaster/keepalived.yaml`

### Deploying OpenShift cluster
As user *openshift* run:

`ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/byo/config.yml`
