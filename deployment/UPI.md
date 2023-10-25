UPI 4.12

# Preparing the CSAH node

Install RHEL 8.6 on the CSAH node. If needed, an additional CSAH node can be added to ensure redundancy.

After the installation is complete, perform the following tasks in the console as user root.

Set the hostname to reflect the naming standards:

`[root@localhost~]# hostnamectl set-hostname <hostname FQDN>`

Create a bridge interface and a bond interface with bridge as the “master” (or primary) interface. Add “slaves” (secondary interfaces) to the bond and then assign an IP address to the bridge interface, as shown in the following example.

**Note**: The assigned IP address must be able to reach the Internet, and the DNS must be able to resolve [subscription.rhsm.redhat.com](http://subscription.rhsm.redhat.com/). 

#Create bridge interface

`nmcli connection add type bridge ifname br0 con-name bridge-br0`

#Create bond interface with bridge bridge-br0 as master

`nmcli connection add type bond con-name bond0 ifname bond0 bond.options "lacp_rate=1,miimon=100,mode=802.3ad,xmit_hash_policy=layer3+4" ipv4.method disabled ipv6.method ignore master bridge-br0`

#Add slaves to bond interfaces, update the interface names in below commands. Run nmcli connection show to fetch available interfaces

`nmcli connection add type ethernet con-name bond-slave-0  ifname <ifname> master bond0 slave-type bond`

`nmcli connection add type ethernet con-name bond-slave-1 ifname <ifname> master bond0 slave-type bond`

#Set IP Address to bridge-br0 interface

`nmcli connection modify bridge-br0 ipv4.method manual ipv4.addresses 192.168.32.20/24 connection.autoconnect yes ipv4.gateway 192.168.32.1  ipv4.dns 192.168.31.50 ipv4.dns-search dcws.lab`

#Bring up bridge-br0 interface

`nmcli connection up bridge-br0`

Enable the ansible-2.9-for-rhel-8-x86_64-rpms repository, and install the required packages:

`subscription-manager register --username <subscription.user> --password <subscription.password> --force`

`subscription-manager attach --pool=<pool id> `

`subscription-manager repos --enable=ansible-2.9-for-rhel-8-x86_64-rpms`
		
Install the following Red Hat Package Manager (RPMs):

`yum install -y jq ansible python3-netaddr git`

Create a user to run the playbooks.

**Note**: Do not use the username core. User core is part of the OpenShift Container Platform cluster configuration and is a predefined user in CoreOS. In the CSAH (primary/secondary), user core is created using Ansible playbooks.

Update password for user using below commands.

`[root@csah-pri ~]# useradd ansible`

`[root@csah-pri ~]# passwd ansible`

As user root, provide sudoers permissions to user ansible by creating anisble file with below content under /etc/sudoers.d:

`[root@csah-pri sudoers.d]# cat /etc/sudoers.d/ansible`

`ansible ALL=(ALL) NOPASSWD: ALL`

As user ansible, set up password-less access to the CSAH FQDN:

`[ansible@csah-pri ~]$ ssh-keygen`

Press enter and go by defaults for the next set of questions

After ssh keys are generated, copy the FQDN of CSAH node.

`[ansible@csah-pri ~]$ ssh-copy-id <FQDN>`

Download the Ansible playbooks from GitHub and check out branch ecws_ocp412 by running:

`[ansible@csah-pri ~]$ git clone https://github.com/dell-esg/openshift-bare-metal.git`

`[ansible@csah-pri ~]$ cd <git clone dir>/openshift-bare-metal`

`[ansible@csah-pri openshift-bare-metal]$ git checkout origin/ecws_ocp412`

**Note**: To create a secondary CSAH node, install Red Hat Enterprise Linux 8 in a CSAH secondary node manually and repeat above steps with necessary modifications.

As user root, add an entry for a secondary CSAH node in the primary CSAH node /etc/hosts file by running:

`[root@csah-pri ~]# cat /etc/hosts`

<IP Address of secondary csah> csah-sec csah-sec.dcws.lab

As user ansible, set up passwordless access from the primary CSAH node to the secondary CSAH node:

`[ansible@csah-pri ~]$ ssh-copy-id <secondary CSAH FQDN>`


# Preparing and running the Ansible playbooks

In the primary CSAH node, prepare and run the Ansible playbooks as user ansible.

Update the nodes_upi.yaml file containing information about the bootstrap, control-plane, and compute nodes.

**Note:** Ensure that you only modify values in the YAML file. Keys must always remain the same.

Run the program to generate inventory file.

**Note**: If the iDRAC user and password are the same across all control-plane and compute nodes, run the program with the --id_user and --id_pass arguments.

`[ansible@csah-pri ]$ cd <git clone dir>/openshift-bare-metal/python`

`[ansible@csah-pri python]$ python3 generate_inventory_file.py –-run --id_user <idrac user> --id_pass <idrac password> –-nodes nodes_upi.yaml`

1.  --run is to build cluster from a bootstrap, master and worker nodes in the same sequence
2.  --add is to add additional master nodes after cluster is set up
3.  --id_user and --id_pass are idrac console credentials
4.  --nodes nodes inventory file
5.  --debug specify debug logs

**Note:** In the argument that is passed, --release 4.12 specifies the OpenShift version and is the only value that the script accepts. 

The following output is displayed. If there is a secondary management node, enter Yes. The IP address that you specify is configured for Keepalived. Ensure that this IP address is not in use. If there is no backup management node, enter No.

`Is there a backup management node [yes/No]: yes`

`Enter backup management node FQDN: csah-sec.dcws.lab`

`Enter the IP address of VIP used for HAProxy:  _<IP>_`

**Inventory file generation inputs menu**

Select each task number and provide the requested input. If you are unsure about what value to enter for an option, accept the default value.

**Note:** Run the program with all the tasks to ensure that all the necessary keys that are used in the Ansible playbooks are generated.

For option 1, specify the directory to which to download the files:

Provide complete path of directory to download OCP 4.12 software bits; default is /home/ansible/files.

Option 1 downloads OpenShift Container Platform 4.12 software from Red Hat into a directory for which user ansible has permissions. This guide assumes that the directory is specified as /home/ansible/files.

For option 2, enter the cluster installation options by selecting 3 node or 5+ node.

OpenShift 4.12 supports the 3 node and 5+ node options. If you select the 3 node option, you are not prompted for information about compute nodes. 

Specify the bonding details of the control-plane nodes in the cluster and provide additional details as appropriate.

Select the interface to be used for DHCP and PXE and select two interfaces to be used for bonding. If only one interface is available, choose No as an option for creating bonds.

**Note**: In this document, the interface that DHCP and the active bond interface use are the same.

Repeat the steps for the remaining control-plane nodes.

After you have entered the control-plane node information, provide the compute node information if you have chosen 5+ node cluster.

For this release, all compute nodes are installed with RHCOS 4.12.

Provide information related to bonding and the interfaces that bonding uses for each compute node.

For option 3, provide details about the disks that are used in control-plane and compute nodes:

Ensure disknames are available. Otherwise OpenShift install fails

**Note**: This guide assumes that the sda disk (RAID in the BOSS card) is used. If necessary, Perc H755N can be used to create RAID on NVMe drives.

For option 4, provide the cluster name and the DNS forwarder and zone file name, if required. 

**Note:** If DNS Forwarder is not required, enter No.

For option 5, provide details for the HTTP web server setup and directory names that are created under /var/www/html:

For option 6, provide details about the default user that is used to install the OpenShift Container Platform cluster, the service network CIDR, pod network CIDR, and any other information to be added in the install-config.yaml file.

For information about the values to be specified for the pod network and the service network, see [sample install-config.yaml file for bare metal](https://docs.openshift.com/container-platform/4.12/installing/installing_bare_metal/installing-bare-metal.html#installation-bare-metal-config-yaml_installing-bare-metal). 

Red Hat specifies the values that are used for the Container Network Interface (CNI). Ensure that these values do not overlap with your existing network.

Select option 7 to review the inventory that you have provided.

**Note:** To modify any values, run the related option again and correct the values.

Select option 8 to perform a YAML dump of all the displayed contents into the generated_inventory file in the current directory (see this [sample file](https://github.com/dell-esg/openshift-bare-metal/blob/ecws_ocp412/ansible/generated_inventory) in GitHub for guidance).

Download the pullsecret file from your [Red Hat](https://cloud.redhat.com/openshift/install/metal/user-provisioned) account (Red Hat account credentials are required) and copy the file contents into the pullsecret file in the directory that contains the OpenShift Container Platform 4.12 software bits.

**Note**: Copy the generated_inventory and ansible.yaml file from the _<git clone dir>_/python/ directory to _<git clone dir>_/ansible directory. Ensure that the pull_secret_file is copied under /home/ansible/files.

As ansible user, run the playbooks:

`[ansible@csah-pri ansible] $ cd /home/ansible/openshift-bare-metal/ansible`

`[ansible@csah-pri ansible] $ ansible-playbook -i generated_inventory ansible.yaml`

The primary CSAH node is installed and configured with HTTP, HAProxy, DHCP, DNS, and PXE services.

**Note**: HTTP, HAProxy, and DNS services are configured for a secondary CSAH node. The Keepalived service is configured in both primary/secondary only when there is a secondary CSAH node.

In addition, the install-config.yaml file is generated, and the ignition config files are created and made available over HTTP.

If any errors occur while the program is running, see the inventory.log file under the _<git clone dir>/python_ directory to determine the cause of the error and how to resolve it.

**Installing a multi-node cluster**

At a high level, creating a multi-node OpenShift Container Platform cluster consists of the following steps:
 1. Create a bootstrap kernel-based virtual machine (KVM). 
 2. Create the control-plane nodes.
 3. Create the compute nodes.

# Creating a bootstrap KVM

Start the cluster installation by creating a bootstrap KVM. The bootstrap KVM creates the persistent control plane that the control-plane nodes manage. The bootstrap KVM is created as a VM using a QEMU emulator in the CSAH node.

To use virt-install to create KVM, the Ansible playbooks generate a command and place it in the bootstrap_command file under the /home/ansible/files directory.

**Note**: Configure the graphical display to ensure that the PXE menu is displayed. If no graphical menu is set, connect to the virtual console in iDRAC and run the command in step 4. Ensure that PXE is enabled through a bridge interface.

Create the bootstrap VM by running

`[root@csah-pri ~] virt-install --name bootstrapkvm --ram 20480 --vcpu 8 --disk path=/home/bootstrapvm-disk.qcow2,format=qcow2,size=200 --os-variant generic --network=bridge=br0,model=virtio,mac=52:54:00:89:91:18 --pxe --boot uefi,hd,network &`

**Note:** Do not change the MAC address. This address is auto-generated and added in the dhcpd.conf file by the Ansible playbooks. Adding the ampersand symbol (&) at the end ensures that the command is run in the background.  
  
Ensure that the partition that is used to save the disk is of sufficient size. This example uses /home and allocates 200G to the _qcow2_ image that is used by the bootstrap KVM. Size is a hard-coded value. Increase the size if there is not enough space.

When the installation process is complete, KVM reboots into the hard disk.

As user core in CSAH, run `ssh bootstrap` to ensure that the correct IP address is assigned to bond0 and verify that ports 6443 and 22623 are listening:

`[core@csah-pri ~]$ ssh bootstrap sudo ss -tulpn | grep -E'6443|22623|2379'`

Allow approximately 15 minutes for the ports to show up as “listening.” If the ports are not listening after 15 minutes, return to step to reinstall the bootstrap.

# Installing the control-plane nodes

To install the control-plane nodes:

1.  Connect to the iDRAC of a control-plane node and open the virtual console.
2.  Ensure that the correct NIC is enabled with PXE.
3.  In the iDRAC UI, click **Configuration** and select **BIOS Settings**. Then:
4.  Expand Network Settings.
5.  Set PXE Device1 to Enabled.
6.  Expand PXE Device1 Settings.
7.  Set the correct NIC as the interface.
8.  Scroll to the bottom of the **Network Settings** section and select **Apply**.
9.  The system boots automatically into the PXE network and displays the PXE menu.
10.  After the installation is complete and before the node reboots into the PXE, ensure that the hard disk is placed above the PXE interface in the boot order:
    1.  Press **F2** to enter **System Setup**.
    2.  Select System BIOS > Boot Settings > UEFI Boot Settings > UEFI Boot Sequence.
    3.  Select **PXE Device 1**.
    4.  Repeat the preceding step until **PXE Device 1** is at the bottom of the boot menu.
    5.  Click **OK**, and then click **Back**.
    6.  Click **Finish** and save the changes.
11.  Let the node boot into the hard drive where the operating system is installed.
12.  After the node comes up, ensure that the correct hostname is displayed  as etcd-0 on the iDRAC console.


**Control-plane node iDRAC console**

Repeat the preceding steps for the remaining two control-plane nodes

After three control-plane nodes are installed and running, from the CSAH node, log in to the bootstrap node as user core and check the status of the bootkube service:

`[core@bootstrap~]$ journalctl -b -f -u bootkube.service`

**Completing the bootstrap setup**

To complete the bootstrap process:

As user core, run the following command on CSAH node inside /home/core directory:

`[core@csah-pri ~]$ ./openshift-install --dir=openshift wait-for bootstrap-complete --log-level debug`

Validate the status of the control-plane nodes and cluster operators:

`[core@csah-pri ~]$ oc get nodes,co`

**Note:** In a three-node cluster, each control plane node has an additional ROLE worker along with the master node. In a five+ node cluster, compute nodes must be in the Ready state before the cluster operator AVAILABLE state is displayed as True.

# Installing compute nodes for a 5+ node cluster

To install the compute nodes:
1.  Connect to the iDRAC of a compute node and open the virtual console.
2.  In the iDRAC UI, click **Configuration** and select **BIOS Settings**.
3.  Expand Network Settings.
4.  Set PXE Device1 to Enabled.
5.  Expand PXE Device1 Settings.
6.  Select the correct **NIC** as the interface.
7.  Scroll to the bottom of the **Network Settings** section and click **Apply**.
8.  The system automatically boots into the PXE network and displays the PXE menu, as shown in the following figure:
9.  Select the compute node name and let the system reboot after the installation. Before the node reboots into the PXE, ensure that the hard disk is placed above the PXE interface in the boot order:
10.  Press **F2** to enter **System Setup**.
11.  Select System BIOS > Boot Settings > UEFI Boot Settings > UEFI Boot Sequence.
12.  Select **PXE Device 1**.
13.  Repeat the preceding step until **PXE Device 1** is at the bottom of the boot menu.
14.  Click **OK**, and then click **Back**.
15.  Click **Finish** and save the changes.
16.  Let the node boot into the hard drive where the operating system is installed

Repeat the preceding steps for the remaining compute nodes.

As user core in CSAH primary node, approve the CSR to ensure that RHCOS-based compute nodes are added in the cluster.

`[core@csah-pri ~]$ oc get csr -o name | xargs oc adm certificate approve`

Verify that all compute nodes are listed and their status is READY.

`oc get nodes`

**Completing the cluster setup**

This section uses openshift for the install_dir variable. See the inventory file under <_git clone dir_>/python/generated_inventory for the value specified for the install_dir variable.

After the bootstrap, control-plane, and compute nodes are installed, complete the cluster setup:

As user core, run the following command to get cluster operators. Ensure that all the operators are set to True in the AVAILABLE column.

`[core@csah-pri ~]$ oc get clusteroperators`

After the verification is complete, run the following command and ensure there are no errors.

`[core@csah-pri ~]$ ./openshift-install --dir=openshift wait-for install-complete --log-level debug`

**Removing the bootstrap node**

A bootstrap node was created as part of the deployment procedure. Now that the OpenShift Container Platform cluster is running, you can remove this node.

Remove the bootstrap node entries - the names, IP addresses, and MAC addresses, along with the bootstrap_node` key

On the CSAH node, run the playbooks as user ansible:

`[ansible@csah-pri ansible]$ ansible-playbook -i generated_inventory ansible.yaml`

If the bootstrap KVM is listed, delete it by running:

`[ansible@csah-pri ansible]$ sudo virsh list`

`[ansible@csah-pri ansible]$ sudo virsh destroy bootstrapkvm`

`[ansible@csah-pri ansible]$ sudo virsh undefine --nvram bootstrapkvm`

Delete the qcow2 image manually if necessary:

`[ansible@csah-pri ansible]$ sudo rm -rf /path-to-file/bootstrapvm-disk.qcow2`

  
# Adding hosts to the cluster

You can scale up an existing OpenShift cluster by adding more compute nodes:

Add a new_compute_nodes key in the nodes.yaml file. Under the new_compute_nodes key, specify values such as the hostname, IP address for ip_os, IP address for ip_idrac, and supported os.

`new_compute_nodes:`

`- name: compute-3`
 
  `ip_os: _<bond IP>_`

  `ip_idrac: _<iDRAC IP>_`

  `os: rhcos`

To add the new compute nodes to the inventory file, run the Python script as ansible user:

`[ansible@csah-pri python]$ cd_<git clone dir>_/python`

`[ansible@csah-pri python]$ python3 generate_inventory_file.py --add --release 4.12 --nodes nodes_upi.yaml --id_user _<idrac user>_ --id_pass _<idrac_password>_`

Specify the bonding information as appropriate. An updated inventory file is created with the new compute node information added.

`Enter complete path to existing inventory file: _<git clone dir>_/ansible/generated_inventory`

`Do you want to perform bonding for 'new_compute_nodes' (y/NO): y`

Run the playbook, update the DNS, DHCP, and HAProxy entries, and set up PXE for the new compute node:

`[ansible@csah-pri ansible]$ pwd`

/home/ansible/openshift-bare-metal/ansible

`[ansible@csah-pri ansible]$ ansible-playbook -i _<updated inventory file>_ ansible.yaml`

To complete the installation, follow the steps in Installing compute nodes.
