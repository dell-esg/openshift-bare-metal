FROM registry.access.redhat.com/rhel7
MAINTAINER Lukasz Sztachanski <lukasz.sztachanski@intel.com>
RUN yum repolist > /dev/null && \
    yum install -y yum-utils && \
    yum-config-manager --disable \* &> /dev/null && \
    yum-config-manager --enable rhel-server-rhscl-7-rpms && \
    yum-config-manager --enable rhel-7-server-rpms && \
    yum-config-manager --enable rhel-7-server-optional-rpms && \
    yum -y update && \
    yum -y install rh-nginx110.x86_64 && \
    yum clean all && sed -i s/80\ default/8080\ default/ \
    /etc/opt/rh/rh-nginx110/nginx/nginx.conf

EXPOSE 8080
USER 999

VOLUME /opt/rh/rh-nginx110/root/usr/share/nginx/html

ENTRYPOINT [ "/opt/rh/rh-nginx110/root/usr/sbin/nginx", "-g", "daemon off;" ]
