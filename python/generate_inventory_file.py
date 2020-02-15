import os
import socket
import sys
import yaml

from urllib.request import urlopen
from urllib.request import urlretrieve

from helper import create_dir, check_path, get_ip, get_network_device_mac, \
                   set_values, validate_cidr, validate_ip, \
                   validate_network_cidr, validate_port, validate_url

class InventoryFile:
    def __init__(self, inventory_dict = {}):
        self.inventory_dict = inventory_dict
        self.software_dir = ''
        self.ocp43_client_base_url = 'https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest-4.3'
        self.ocp43_rhcos_base_url = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/latest/4.3.0'
        self.ocp_urls = {'openshift_client': '{}/openshift-client-linux-4.3.1.tar.gz'.format(self.ocp43_client_base_url),
                         'openshift_installer': '{}/openshift-install-linux-4.3.1.tar.gz'.format(self.ocp43_client_base_url),
                         'initramfs': '{}/rhcos-4.3.0-x86_64-installer-initramfs.img'.format(self.ocp43_rhcos_base_url),
                         'kernel_file': '{}/rhcos-4.3.0-x86_64-installer-kernel'.format(self.ocp43_rhcos_base_url),
                         'uefi_file': '{}/rhcos-4.3.0-x86_64-metal.raw.gz'.format(self.ocp43_rhcos_base_url)}

    def clear_screen(self):
        os.system('clear')

    def set_keys(self):
        self.inventory_dict['csah'] = {'hosts': '{}'.format(socket.getfqdn()), 'vars': {}}

    def get_software_download_dir(self):
        self.clear_screen()
        default = '/home/ansible/files'
        self.software_dir = input('provide complete path of directory to download OCP 4.3 software bits\n'
                                  'default [/home/ansible/files]: ')
        self.software_dir = set_values(self.software_dir, default)
        dest_path_exist = check_path(self.software_dir, isdir=True)
        if dest_path_exist:
            print('directory {} already exists'.format(self.software_dir))
        else:
            print('Creating directory {}'.format(self.software_dir))
            create_dir(self.software_dir)

        self.inventory_dict['csah']['vars']['software_src'] = self.software_dir

    def get_software(self):

        for url_key in self.ocp_urls.keys():
            url = self.ocp_urls[url_key]
            dest_name = url.split('/')[-1]
            dest_path = self.software_dir + '/' + dest_name
            dest_path_exist = check_path(dest_path, isfile=True)
            url_check = ''
            if dest_path_exist:
                print('file {} already exists in {}'.format(dest_name, self.software_dir))
                self.inventory_dict['csah']['vars'][url_key] = dest_name
   
            else:
                url_check = urlopen(url)

            if url_check != '' and url_check.code == 200:
                print('downloading {}'.format(dest_name))
                urlretrieve('{}'.format(url),'{}/{}'.format(self.software_dir, dest_name))
                self.inventory_dict['csah']['vars'][url_key] = dest_name

            if url_check != '' and url_check.code != 200:
                print('url validation error {}'.format(dest_name))

    def get_bootstrap_node(self):
        self.clear_screen()
        default = 'bootstrap'
        bootstrap_name = input('enter the master {} node name\n' 
                               'default [bootstrap]:'.format(num))
        bootstrap_name = set_values(bootstrap_name, default)
        bootstrap_ip = get_ip(node_type='bootstrap', ip_type='os')
        bootstrap_ip = validate_ip(bootstrap_ip)
        bootstrap_mac = get_network_device_mac(node_type='bootstrap', ip_type='idrac')
        self.inventory_dict['csah']['vars']['bootstrap_node'] = [{'name': '{}'.format(bootstrap_name),
                                                                  'ip': '{}'.format(bootstrap_ip),
                                                                  'mac': '{}'.format(bootstrap_mac)}]
        
    def get_master_nodes(self):
        self.clear_screen()   
        master_nodes_count = int(input('enter number of master nodes: '))
        master_keys = ['name','ip','mac']
        self.inventory_dict['csah']['vars']['master_nodes'] = []
        for num in range(master_nodes_count):
            master_values = []
            node_type = 'master{}'.format(num)
            default = 'etcd-{}'.format(num)
            master_name = input('enter the master {} node name \n'
                                'default [{}]:'.format(num, default))
            master_name = set_values(master_name, default)
            master_ip = get_ip(node_type=node_type, ip_type='os')
            master_mac = get_network_device_mac(node_type=node_type, ip_type='idrac')
            master_values.append(master_name)
            master_values.append(master_ip)
            master_values.append(master_mac)
            master_node_dict_pairs = dict(zip(master_keys, master_values))
            self.inventory_dict['csah']['vars']['master_nodes'].append(master_node_dict_pairs)
        self.inventory_dict['csah']['vars']['number_of_masters'] = master_nodes_count
            
    def get_worker_nodes(self):
        self.clear_screen()   
        worker_nodes_count = int(input('enter number of worker nodes: '))
        worker_keys = ['name','ip','mac']
        self.inventory_dict['csah']['vars']['worker_nodes'] = []
        for num in range(worker_nodes_count):
            worker_values = []
            node_type = 'worker{}'.format(num)
            default = 'worker{}'.format(num)
            worker_name = input('enter the worker {} node name\n'
                                'default [{}]'.format(num, default))
            worker_name = set_values(worker_name, default)
            worker_ip = get_ip(node_type=node_type, ip_type='os')
            worker_mac = get_network_device_mac(node_type=node_type, ip_type='idrac')
            worker_values.append(worker_name)
            worker_values.append(worker_ip)
            worker_values.append(worker_mac)
            worker_node_dict_pairs = dict(zip(worker_keys, worker_values))
            self.inventory_dict['csah']['vars']['worker_nodes'].append(worker_node_dict_pairs)
        self.inventory_dict['csah']['vars']['number_of_workers'] = worker_nodes_count

    def set_bond_network_details(self):
        self.clear_screen()   
        name = input('enter bond name: ')
        interfaces = input('enter bond interfaces seperated by ,\n'
                           ' default [ens2f0,ens2f1]: ')
        default = 'ens2f0,ens2f1'
        interfaces = set_values(interfaces, default)
        default = 'active-backup,miimon=100,primary=ens2f0'
        options = input('enter bond options \n'
                        'default [active-backup,miimon=100,primary=ens2f0]: ')
        options = set_values(options, default)
        self.inventory_dict['csah']['vars']['bond_name'] = name
        self.inventory_dict['csah']['vars']['bond_interfaces'] = interfaces
        self.inventory_dict['csah']['vars']['bond_options'] = options
        
    def get_dns_details(self):
        self.clear_screen()
        zone_file = input('specify zone file \n'
                          'default [/var/named/ocp.zones]: ')
        default = '/var/named/ocp.zones'
        zone_file = set_values(zone_file, default)
        cluster_name = input('specify cluster name \n'
                             'default [ocp]: ')
        default = 'ocp'
        cluster_name = set_values(cluster_name, default)
        self.inventory_dict['csah']['vars']['default_zone_file'] = zone_file
        self.inventory_dict['csah']['vars']['cluster'] = cluster_name

    def get_http_details(self):
        self.clear_screen()
        port = input('enter http port \n'
                     'default [8080]: ')
        default = 8080
        port = set_values(port, default)
        port = validate_port(port)
        ignition_dir = input('specify dir where ignition files will be placed \n '
                             'directory will be created under /var/www/html \n'
                             'default [ignition]: ')
        default = 'ignition'
        ignition_dir = set_values(ignition_dir, default)
        ocp_version = input('specify the version of ocp \n'
                            'default [4.3]: ')
        default = 4.3
        ocp_version = set_values(ocp_version, default)
        self.inventory_dict['csah']['vars']['http_port'] = int(port)
        self.inventory_dict['csah']['vars']['os'] = 'rhcos'
        self.inventory_dict['csah']['vars']['http_ignition'] = ignition_dir
        self.inventory_dict['csah']['vars']['version'] = ocp_version

    def get_disk_name(self):
        self.clear_screen()
        default = 'nvme0n1'
        print('ensure disknames are absolutely available. Otherwise OpenShift install fails')
        master_install_device = input('specify the master device that will be installed\n '
                                      'default [nvme0n1]: ')
        master_install_device = set_values(master_install_device, default)
        bootstrap_install_device = input('specify the bootstrap device that will be installed\n '
                                         'default [nvme0n1]: ')
        bootstrap_install_device = set_values(bootstrap_install_device, default)
        worker_install_device = input('specify the worker device that will be installed\n '
                                      'default [nvme0n1]: ')
        worker_install_device = set_values(worker_install_device, default)
        self.inventory_dict['csah']['vars']['master_install_device'] = master_install_device
        self.inventory_dict['csah']['vars']['bootstrap_install_device'] = bootstrap_install_device
        self.inventory_dict['csah']['vars']['worker_install_device'] = worker_install_device

    def set_haproxy(self):
        print('currently only haproxy is supported for load balancing')
        self.inventory_dict['csah']['vars']['proxy'] = 'haproxy'
        self.inventory_dict['csah']['vars']['haproxy_conf'] = '/etc/haproxy/haproxy.cfg'
        self.inventory_dict['csah']['vars']['master_ports'] = [{'port': 6443, 'description': 'apiserver'},
                                                               {'port': 22623 , 'description': 'configserver'}]
        self.inventory_dict['csah']['vars']['worker_ports'] = [{'port': 80, 'description': 'http'},
                                                               {'port': 443, 'description': 'https'}]

    def get_ignition_details(self):
        self.clear_screen()
        default = 'core'
        install_user = input('enter the user used to install openshift\n '
                             'DONOT CHANGE THIS VALUE'
                             'default [core]: ')
        install_user = set_values(install_user, default)
        default = 'openshift'
        install_dir = input('enter the directory where openshift installs\n '
                            'directory will be created under /home/core'
                            'default [openshift]: ')
        install_dir = set_values(install_dir, default)
        default = '10.128.0.0/14'
        pod_network_cidr = input('enter the pod network cidr\n '
                                 'default [10.128.0.0/14]: ')
        pod_network_cidr = set_values(pod_network_cidr, default)
        pod_network_cidr = validate_network_cidr(pod_network_cidr)
        default = 23
        host_prefix = input('specify cidr notation for number of ips in each node: \n '
                            'cidr number should be an integer and less than 32\n '
                            'default [23]: ')
        host_prefix = set_values(host_prefix, default)
        host_prefix = validate_cidr(host_prefix)
        default = '172.30.0.0/16'
        service_network_cidr = input('specify the service network cidr\n '
                                     'default [172.30.0.0/16]: ')
        service_network_cidr = set_values(service_network_cidr, default)
        service_network_cidr = validate_network_cidr(service_network_cidr)
        self.inventory_dict['csah']['vars']['install_user'] = install_user
        self.inventory_dict['csah']['vars']['install_dir'] = install_dir
        self.inventory_dict['csah']['vars']['cluster_network_cidr'] = pod_network_cidr
        self.inventory_dict['csah']['vars']['host_prefix'] = host_prefix
        self.inventory_dict['csah']['vars']['service_network_cidr'] = service_network_cidr
            
    def yaml_inventory(self):
        ansible_inventory = [self.inventory_dict]
        print(yaml.dump(ansible_inventory[0], sort_keys=False))

    def run(self):
        self.set_keys()
        self.get_software_download_dir()
        self.get_software()
        self.get_bootstrap_node()
        self.get_master_nodes()
        self.get_worker_nodes()
        self.set_bond_network_details()
        self.get_dns_details()
        self.get_http_details()
        self.get_disk_name()
        self.set_haproxy()
        self.get_ignition_details()
        self.yaml_inventory()

def main():
    gen_inv_file = InventoryFile()
    gen_inv_file.run()


if __name__ == "__main__":
    main()
