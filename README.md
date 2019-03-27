# Deploying Red Hat OpenShift® Container Platform 3.11 with OpenShift Container Storage

## Instructions
Please refer to the [Reference Architecture document](https://dellemc.com/openshift/xxx) for network diagrams and detailed server information.

Though some of these commands can be run as a non-root user, it is assumed they are being run as root unless stated otherwise.

### Clone the repository
```bash
$ git clone https://github.com/dell/openshift-bare-metal.git
```

### Populating the inventory file
The inventory file has to be filled manually.
Refer to `hosts.example.com` for possible variables.

```bash
$ cd openshift-bare-metal
$ cp hosts.example.com /etc/ansible/hosts
$ vim /etc/ansible/hosts
```
### Provisioning system setup
Following script builds OS provisioning framework and templates according to an inventory file:
```
# ansible-playbook src/ipxe-deployer/ipxe.yml
```
Servers need to boot from PXE.
Refer to playbooks from section **Power Management**.

### Preparing the nodes for OpenShift Container Platform
```bash
$ ansible-playbook src/prerequisites/nodes_setup.yaml -k
```

### Setting up multimaster HA
```bash
$ ansible-playbook src/keepalived-multimaster/keepalived.yaml
```

### Deploying Red Hat OpenShift Container Platform cluster
```bash
$ ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/prerequisites.yml
$ ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/deploy_cluster.yml
```
### Deploy NVMe Storage Class (requires an openshift user login with "cluster-admin" role) 
##  Run Ansible playbook to expose the R740xd NVMe storage, make it the default Storage Class and available to Red Hat OpenShift users.
$ ansible-playbook src/ocs-pool/storage-class.yml
$ oc get sc 

### Support
Please note that this code is provided as-is and is supported by the community. If you have specific support questions, please e-mail openshift@dell.com.
