# Deploying Red Hat OpenShift® Container Platform 3.10 with Container-Native Storage

## Instructions
Please refer to [Reference Architecture document](https://tbd.pdf) for detailed instructions.

### Clone the repository
`$ git clone https://github.com/dell/openshift-container-architecture.git`

### Populating inventory file
The inventory file has to be filled manually.
Refer to *hosts.fv4* for possible variables.

```
$ cp hosts.fv4 /etc/ansible/hosts
$ vim /etc/ansible/hosts
```

### Switch Configuration
The Dell OS10 configuration role requires Ansible v2.5, which we will use via a Docker container. First, build the container image (install Docker if not already installed):

```
$ cd src/os10-configuration
$ docker build -t ansible25 .
```

Then, update the dellos10 section in the inventory file with your IP addresses and credentials and copy to the current directory (since we are volume-mounting the current directory inside the container):

```
$ vim /etc/ansible/hosts			# update accordingly
$ cp /etc/ansible/hosts .
$ docker run --rm -it -v $PWD:/playbooks ansible25 -i hosts configure_dellos10.yaml`
```

### Server BIOS configuration
We need to configure some options in the server BIOS like enabling PXE booting from the correct NICs. We will do so using the Server Configuration Profile (SCP).
We need to setup an NFS share with 2 SCP files, so update *inventory_scp_setup.yaml* with the IP address of your bastion node in the **management** network and run:

`$ ansible-playbook -i src/scp_configuration/inventory_scp_setup.yaml src/scp_configuration/setup_scp_environment.yaml`

Next, update *inventory_scp_apply.yaml* and run:

`$ ansible-playbook -i src/scp_configuration/inventory_scp_apply.yaml src/scp_configuration/bios_settings.yaml`

This will:

- Enable IPMI
- Disable PXE for embedded NIC port 1
- Enable PXE for addon NIC port 1
- Setup boot order: 1) BOSS cards 2) NIC

To do a one time boot from NIC:

`$ ansible-playbook -i src/scp_configuration/inventory_scp_apply.yaml src/scp_configuration/one_time_boot.yaml`

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
$ su - openshift
$ ansible-playbook src/keepalived-multimaster/keepalived.yaml
```

### Deploying OpenShift cluster
As user *openshift* run:

`$ ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/byo/config.yml`
