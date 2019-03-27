#bare minimum hostfile OCP 3.11.88 ocp.example.com
[OSEv3:children]
masters
nodes
etcd

[OSEv3:vars]
openshift_release=3.11.88
openshift_deployment_type=openshift-enterprise
openshift_portal_net=172.30.0.0/16
# localhost likely doesn't meet the minimum requirements
openshift_disable_check=disk_availability,memory_availability
openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider'}]
openshift_master_htpasswd_users={'admin': '$apr1$8FIlD2Y3$DXZdxXxQFyPvsow0hc2.71'}

openshift_node_groups=[{'name': 'node-config-all-in-one', 'labels': ['node-role.kubernetes.io/master=true', 'node-role.kubernetes.io/infra=true', 'node-role.kubernetes.io/compute=true']}]

openshift_master_api_port=8443
openshift_master_console_port=8443

#Default:  openshift_master_cluster_method=native
# Internal cluster name
openshift_master_cluster_hostname=ocp.example.com

# NOTE: Default wildcard domain for applications
openshift_master_default_subdomain=apps.ocp.example.com

[masters]
localhost ansible_connection=local

[etcd]
localhost ansible_connection=local

[nodes]
# openshift_node_group_name should refer to a dictionary with matching key of name in list openshift_node_groups.
localhost ansible_connection=local openshift_node_group_name="node-config-all-in-one"

[nodes:vars]
oreg_auth_user=YourRHaccount
oreg_auth_password=YourRHpassword
oreg_url=registry.redhat.io/openshift3/ose-${component}:${version}
openshift_examples_modify_imagestreams=false
