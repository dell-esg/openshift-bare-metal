FROM registry.access.redhat.com/rhel7/rhel
MAINTAINER Jose Delarosa "https://github.com/jose-delarosa"

# Install Ansible v2.5
RUN yum-config-manager --enable rhel-7-server-ansible-2.5-rpms > /dev/null && \
    yum -y install ansible openssh-clients

ENV ANSIBLE_GATHERING smart
ENV ANSIBLE_HOST_KEY_CHECKING false
ENV ANSIBLE_ROLES_PATH /playbooks/roles
ENV ANSIBLE_SSH_PIPELINING True

# Set running environment
WORKDIR /playbooks
ENTRYPOINT ["ansible-playbook", "-i", "inventory.yaml"]
