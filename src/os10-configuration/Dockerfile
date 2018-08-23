FROM registry.access.redhat.com/rhel7/rhel
MAINTAINER Jose Delarosa "https://github.com/jose-delarosa"

# Install Ansible v2.5
RUN yum-config-manager --enable rhel-7-server-ansible-2.5-rpms && \
    yum -y install ansible

# Set running environment
WORKDIR /playbooks
ENTRYPOINT ["ansible-playbook", "-i", "inventory.yaml"]
