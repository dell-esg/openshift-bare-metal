[OSEv3:children]
masters
nodes
etcd
lb
local
glusterfs
glusterfs_registry

[OSEv3:vars]
openshift_release=v3.11
openshift_deployment_type=openshift-enterprise

ansible_ssh_user=root
root_password="OS_PASSWORD"

openshift_storage_glusterfs_image=registry.access.redhat.com/rhgs3/rhgs-server-rhel7:v3.11
openshift_storage_glusterfs_block_image=registry.access.redhat.com/rhgs3/rhgs-gluster-block-prov-rhel7:v3.11
openshift_storage_glusterfs_heketi_image=registry.access.redhat.com/rhgs3/rhgs-volmanager-rhel7:v3.11

openshift_master_cluster_method=native
openshift_master_cluster_hostname=r5a.local
openshift_master_cluster_public_hostname=ocp.example.com
openshift_master_default_subdomain=apps.ocp.example.com
openshift_master_cluster_ip=192.168.20.99
openshift_master_cluster_public_ip=100.82.42.99
openshift_master_portal_net=10.0.0.0/16
openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider'}]
openshift_master_htpasswd_users={'admin': '$apr1$i4wJZDXxXdKhqHNvPCzTcXAt99Gooz0'}
openshift_clock_enabled=true
os_sdn_network_plugin_name='redhat/openshift-ovs-multitenant'
 
# logging
openshift_logging_install_logging=true
openshift_logging_es_pvc_dynamic=true 
openshift_logging_es_pvc_size=200Gi
openshift_logging_es_cluster_size=3
openshift_logging_es_pvc_storage_class_name='glusterfs-registry-block'
openshift_logging_kibana_nodeselector={"node-role.kubernetes.io/infra": "true"}
openshift_logging_curator_nodeselector={"node-role.kubernetes.io/infra": "true"}
openshift_logging_es_nodeselector={"node-role.kubernetes.io/infra": "true"}
 
# metrics
openshift_metrics_install_metrics=true 
openshift_metrics_storage_kind=dynamic
openshift_metrics_storage_volume_size=200Gi
openshift_metrics_cassandra_pvc_storage_class_name='glusterfs-registry-block'
openshift_metrics_hawkular_nodeselector={"node-role.kubernetes.io/infra": "true"}
openshift_metrics_cassandra_nodeselector={"node-role.kubernetes.io/infra": "true"}
openshift_metrics_heapster_nodeselector={"node-role.kubernetes.io/infra": "true"}

# registry
openshift_master_dynamic_provisioning_enabled=True
openshift_hosted_registry_storage_kind=glusterfs
openshift_hosted_registry_storage_volume_size=1000Gi
openshift_hosted_registry_selector="node-role.kubernetes.io/infra=true"
 
# OCS storage cluster for applications
openshift_storage_glusterfs_namespace=app-storage
openshift_storage_glusterfs_storageclass=true
openshift_storage_glusterfs_storageclass_default=false
openshift_storage_glusterfs_block_deploy=false
 
# OCS storage for OpenShift infrastructure
openshift_storage_glusterfs_registry_namespace=infra-storage
openshift_storage_glusterfs_registry_storageclass=false
openshift_storage_glusterfs_registry_block_deploy=true
openshift_storage_glusterfs_registry_block_host_vol_create=true
openshift_storage_glusterfs_registry_block_host_vol_size=500
openshift_storage_glusterfs_registry_block_storageclass=true
openshift_storage_glusterfs_registry_block_storageclass_default=false
 
# Red Hat Subscription information. Use user and password OR activation key and organization id.
rhel_subscription_user=YourRHaccount
rhel_subscription_pass=YourRHpassword
activationkey=xxxxxxxxx
org_id=xxxxxxxx

# Network settings. Required for OS provisioning. Modify for your public network. 
dns_local=192.168.20.11
dns_upstream=100.82.42.8
external_interface=bond0
external_vlan=421
external_netmask=255.255.255.0
external_gateway=100.82.42.1
internal_interface=bond0
internal_netmask=255.255.255.0
internal_gateway={{ bastion_ip }}
bastion_ip=192.168.20.11
dhcp_first_ip=192.168.20.100
dhcp_last_ip=192.168.20.150

[local]
127.0.0.1

[masters]
master1.r5a.local
master2.r5a.local
master3.r5a.local

[etcd]
master1.r5a.local
master2.r5a.local
master3.r5a.local

[lb]
infra1.r5a.local
infra2.r5a.local
infra3.r5a.local

[glusterfs]
stor1.r5a.local glusterfs_cluster=1 glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1", "/dev/nvme4n1", "/dev/nvme5n1", "/dev/nvme6n1", "/dev/nvme7n1", "/dev/nvme8n1", "/dev/nvme9n1", "/dev/nvme10n1", "/dev/nvme11n1" ]'
stor2.r5a.local glusterfs_cluster=1 glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1", "/dev/nvme4n1", "/dev/nvme5n1", "/dev/nvme6n1", "/dev/nvme7n1", "/dev/nvme8n1", "/dev/nvme9n1", "/dev/nvme10n1", "/dev/nvme11n1" ]'
stor3.r5a.local glusterfs_cluster=1 glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1", "/dev/nvme4n1", "/dev/nvme5n1", "/dev/nvme6n1", "/dev/nvme7n1", "/dev/nvme8n1", "/dev/nvme9n1", "/dev/nvme10n1", "/dev/nvme11n1" ]'
stor4.r5a.local glusterfs_cluster=1 glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1", "/dev/nvme4n1", "/dev/nvme5n1", "/dev/nvme6n1", "/dev/nvme7n1", "/dev/nvme8n1", "/dev/nvme9n1", "/dev/nvme10n1", "/dev/nvme11n1" ]'

[glusterfs_registry]
infra1.r5a.local glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1" ]'
infra2.r5a.local glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1" ]'
infra3.r5a.local glusterfs_devices='[ "/dev/nvme2n1", "/dev/nvme3n1" ]'

[nodes]
master1.r5a.local openshift_ip=192.168.20.12 openshift_hostname=master1.r5a.local idrac_ip=192.168.10.12 serial=DELL_SVCTAG1 openshift_node_group_name='node-config-master'
master2.r5a.local openshift_ip=192.168.20.13 openshift_hostname=master2.r5a.local idrac_ip=192.168.10.13 serial=DELL_SVCTAG2 openshift_node_group_name='node-config-master'
master3.r5a.local openshift_ip=192.168.20.14 openshift_hostname=master3.r5a.local idrac_ip=192.168.10.14 serial=DELL_SVCTAG3 openshift_node_group_name='node-config-master'

infra1.r5a.local openshift_ip=192.168.20.15 openshift_hostname=infra1.r5a.local idrac_ip=192.168.10.15 serial=DELL_SVCTAG4 openshift_node_group_name='node-config-infra' openshift_public_ip=100.82.42.15
infra2.r5a.local openshift_ip=192.168.20.16 openshift_hostname=infra2.r5a.local idrac_ip=192.168.10.16 serial=DELL_SVCTAG5 openshift_node_group_name='node-config-infra' openshift_public_ip=100.82.42.16
infra3.r5a.local openshift_ip=192.168.20.17 openshift_hostname=infra3.r5a.local idrac_ip=192.168.10.17 serial=DELL_SVCTAG6 openshift_node_group_name='node-config-infra' openshift_public_ip=100.82.42.17

app1.r5a.local openshift_ip=192.168.20.18 openshift_hostname=app1.r5a.local idrac_ip=192.168.10.18 serial=DELL_SVCTAG7 openshift_node_group_name='node-config-compute' 
app2.r5a.local openshift_ip=192.168.20.19 openshift_hostname=app2.r5a.local idrac_ip=192.168.10.19 serial=DELL_SVCTAG8 openshift_node_group_name='node-config-compute' 
app3.r5a.local openshift_ip=192.168.20.20 openshift_hostname=app3.r5a.local idrac_ip=192.168.10.20 serial=DELL_SVCTAG9 openshift_node_group_name='node-config-compute' 
app4.r5a.local openshift_ip=192.168.20.21 openshift_hostname=app4.r5a.local idrac_ip=192.168.10.21 serial=DELL_SVCTAG10 openshift_node_group_name='node-config-compute' 

stor1.r5a.local openshift_ip=192.168.20.22 openshift_hostname=stor1.r5a.local idrac_ip=192.168.10.22 serial=DELL_SVCTAG11 openshift_node_group_name='node-config-compute' interface3='p7p1' interface4='p7p2'
stor2.r5a.local openshift_ip=192.168.20.23 openshift_hostname=stor2.r5a.local idrac_ip=192.168.10.23 serial=DELL_SVCTAG12 openshift_node_group_name='node-config-compute' interface3='p7p1' interface4='p7p2'
stor3.r5a.local openshift_ip=192.168.20.24 openshift_hostname=stor3.r5a.local idrac_ip=192.168.10.24 serial=DELL_SVCTAG13 openshift_node_group_name='node-config-compute' interface3='p7p1' interface4='p7p2'
stor4.r5a.local openshift_ip=192.168.20.25 openshift_hostname=stor4.r5a.local idrac_ip=192.168.10.25 serial=DELL_SVCTAG14 openshift_node_group_name='node-config-compute' interface3='p7p1' interface4='p7p2'

[nodes:vars]
idrac_user=root
idrac_password=iDRAC_PASSWORD

oreg_auth_user=YourRHaccount
oreg_auth_password=YourRHpassword

oreg_url=registry.redhat.io/openshift3/ose-${component}:${version}
openshift_examples_modify_imagestreams=true
