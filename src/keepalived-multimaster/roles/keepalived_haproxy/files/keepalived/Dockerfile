FROM registry.access.redhat.com/rhel7
RUN yum -y update && \
    yum -y install keepalived ipset-libs && \
    yum clean all
CMD ["keepalived", "-n", "-P", "-l", "-f", "/etc/keepalived/keepalived.cfg", "-D"]
