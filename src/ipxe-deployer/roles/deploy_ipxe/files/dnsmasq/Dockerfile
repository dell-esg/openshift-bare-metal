FROM registry.access.redhat.com/rhel7
MAINTAINER Lukasz Sztachanski <lukasz.sztachanski@intel.com>
RUN yum -y update && yum -y install dnsmasq && yum clean all

VOLUME /tftp
VOLUME /etc/dnsmasq.d

EXPOSE 53 53/udp 67 67/udp

ENTRYPOINT ["dnsmasq", "-k", "--conf-file=/etc/dnsmasq.conf", "--no-daemon"]
