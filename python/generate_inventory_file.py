import os
import logging
import socket
import sys
import yaml

from urllib.request import urlopen
from urllib.request import urlretrieve

from log_config import log_setup
from helper import create_dir, check_path, get_ip, get_network_device_mac, \
                   set_values, validate_cidr, validate_ip, \
                   validate_network_cidr, validate_port, validate_url, \
                   check_user_input_if_integer

class InventoryFile:
    def __init__(self, inventory_dict = {}):
        self.inventory_dict = inventory_dict
        self.software_dir = ''
        self.input_choice = ''
        self.ocp43_client_base_url = 'https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest-4.3'
        self.ocp43_rhcos_base_url = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/latest/4.3.0'
        self.ocp_urls = {'openshift_client': '{}/openshift-client-linux.tar.gz'.format(self.ocp43_client_base_url),
                         'openshift_installer': '{}/openshift-install-linux.tar.gz'.format(self.ocp43_client_base_url),
                         'initramfs': '{}/rhcos-4.3.0-x86_64-installer-initramfs.img'.format(self.ocp43_rhcos_base_url),
                         'kernel_file': '{}/rhcos-4.3.0-x86_64-installer-kernel'.format(self.ocp43_rhcos_base_url),
                         'uefi_file': '{}/rhcos-4.3.0-x86_64-metal.raw.gz'.format(self.ocp43_rhcos_base_url)}
        self.task_inputs = """
1: 'download ocp 4.3 software',
2: 'bootstrap node details',
3: 'master node details',
4: 'worker node details',
5: 'network setup',
6: 'disk info',
7: 'bind dns',
8: 'http webserver',
9: 'dhcp',
10: 'ignition config',
11: 'print inventory',
12: 'generate inventory file',
13: 'Exit'
"""                 

    def clear_screen(self):
        """ 
        performs clean screen

        """
        os.system('clear')

    def set_keys(self):
        """ 
        sets the initial keys for the inventory file

        """
        self.inventory_dict['csah'] = {'hosts': '{}'.format(socket.getfqdn()), 'vars': {}}

    def generate_inputs_menu(self):
        """
        generates a menu of tasks for user input for each task
 
        """
        self.clear_screen()
        self.input_choice = ''
        valid_choices = range(1,14)
        while self.input_choice not in valid_choices:
             logging.info('{}'.format(self.task_inputs))
             try:
                 self.input_choice = int(input('task choice for necessary inputs: '))
                 if self.input_choice not in valid_choices:
                     logging.warn('Invalid choice. Valid choice is an integer from 1-13')
             except ValueError:
                 logging.error('Strings not a valid choice')

        logging.info('user choice is {}'.format(self.input_choice))
        self.get_user_inputs_for_task()
            
    def get_user_inputs_for_task(self):
        """ 
        performs tasks based on user input

        """
        if self.input_choice == 13:
            sys.exit()
        elif self.input_choice == 1:
            self.get_software_download_dir()
            self.get_software()
        elif self.input_choice == 2:
            self.get_bootstrap_node()
        elif self.input_choice == 3:
            self.get_master_nodes()
        elif self.input_choice == 4:
            self.get_worker_nodes()
        elif self.input_choice == 5:
            self.set_bond_network_details()
        elif self.input_choice == 6:
            self.get_disk_name()
        elif self.input_choice == 7:
            self.get_dns_details()
        elif self.input_choice == 8:
            self.get_http_details()
        elif self.input_choice == 9:
            self.dhcp_lease_times()
        elif self.input_choice == 10:
            self.get_ignition_details()
        elif self.input_choice == 11:
            self.display_inventory()
        elif self.input_choice == 12:
            self.yaml_inventory()
            sys.exit()
        self.generate_inputs_menu()

    def get_software_download_dir(self):
        """ 
        get software download directory to download OCP 4.3 software bits
  
        """
        self.clear_screen()
        default = '/home/ansible/files'
        self.software_dir = input('provide complete path of directory to download OCP 4.3 software bits\n'
                                  'default [/home/ansible/files]: ')
        self.software_dir = set_values(self.software_dir, default)
        dest_path_exist = check_path(self.software_dir, isdir=True)
        if dest_path_exist:
            logging.info('directory {} already exists'.format(self.software_dir))
        else:
            logging.info('Creating directory {}'.format(self.software_dir))
            create_dir(self.software_dir)

        self.inventory_dict['csah']['vars']['software_src'] = self.software_dir

    def get_software(self):
        """ 
        performs OCP 4.3 software bits download from the base urls
        specified in the class __init__ 
   
        """

        logging.info('downloading OCP 4.3 software bits into {}'.format(self.software_dir))
        for url_key in self.ocp_urls.keys():
            url = self.ocp_urls[url_key]
            dest_name = url.split('/')[-1]
            dest_path = self.software_dir + '/' + dest_name
            dest_path_exist = check_path(dest_path, isfile=True)
            url_check = ''
            if dest_path_exist:
                logging.info('file {} already exists in {}'.format(dest_name, self.software_dir))
                self.inventory_dict['csah']['vars'][url_key] = dest_name
            else:
                url_check = validate_url(url)
                if url_check == '':
                    logging.error('file {} in {} is not available'.format(dest_name, url_key))
                    self.inventory_dict['csah']['vars'][url_key] = ''

            if url_check != '' and url_check.code == 200:
                logging.info('downloading {}'.format(dest_name))
                urlretrieve('{}'.format(url),'{}/{}'.format(self.software_dir, dest_name))
                self.inventory_dict['csah']['vars'][url_key] = dest_name

    def get_bootstrap_node(self):
        """ 
        get details about bootstrap node

        """
        self.clear_screen()
        default = 'bootstrap'
        bootstrap_name = input('enter the bootstrap node name\n'
                               'default [bootstrap]: ')
        bootstrap_name = set_values(bootstrap_name, default)
        bootstrap_ip = get_ip(node_name=bootstrap_name, ip_type='os')
        bootstrap_ip = validate_ip(bootstrap_ip)
        bootstrap_mac = get_network_device_mac(node_name=bootstrap_name, ip_type='idrac')
        logging.info('adding bootstrap_node values as name: {} ip: {} mac: {}'.format(bootstrap_name, bootstrap_ip,
                                                                                      bootstrap_mac)) 
        self.inventory_dict['csah']['vars']['bootstrap_node'] = [{'name': '{}'.format(bootstrap_name),
                                                                  'ip': '{}'.format(bootstrap_ip),
                                                                  'mac': '{}'.format(bootstrap_mac)}]

    def get_master_nodes(self):
        """ 
        get details about master node

        """
        default = 3
        master_nodes_count = input('enter number of master nodes\n'
                                   'default [3]: ')
        master_nodes_count = set_values(master_nodes_count, default, check='integer')
        master_keys = ['name','ip','mac']
        self.inventory_dict['csah']['vars']['master_nodes'] = []
        for num in range(master_nodes_count):
            master_values = []
            default = 'etcd-{}'.format(num)
            master_name = input('enter the master {} node name \n'
                                'default [{}]: '.format(num, default))
            master_name = set_values(master_name, default)
            master_ip = get_ip(node_name=master_name, ip_type='os')
            master_mac = get_network_device_mac(node_name=master_name, ip_type='idrac')
            master_values.append(master_name)
            master_values.append(master_ip)
            master_values.append(master_mac)
            master_node_dict_pairs = dict(zip(master_keys, master_values))
            logging.info('adding {} values as name: {} ip: {} mac: {}'.format(master_name, master_name,
                                                                              master_ip, master_mac)) 
            self.inventory_dict['csah']['vars']['master_nodes'].append(master_node_dict_pairs)
            self.clear_screen()
        self.inventory_dict['csah']['vars']['number_of_masters'] = master_nodes_count

    def get_worker_nodes(self):
        """ 
        get details about worker node

        """
        worker_nodes_count = input('enter number of worker nodes\n'
                                   'default [2]: ')
        default = 2
        worker_nodes_count = set_values(worker_nodes_count, default, check='integer')
        worker_keys = ['name','ip','mac']
        self.inventory_dict['csah']['vars']['worker_nodes'] = []
        for num in range(worker_nodes_count):
            worker_values = []
            default = 'worker-{}'.format(num)
            worker_name = input('enter the worker {} node name\n'
                                'default [{}]: '.format(num, default))
            worker_name = set_values(worker_name, default)
            worker_ip = get_ip(node_name=worker_name, ip_type='os')
            worker_mac = get_network_device_mac(node_name=worker_name, ip_type='idrac')
            worker_values.append(worker_name)
            worker_values.append(worker_ip)
            worker_values.append(worker_mac)
            worker_node_dict_pairs = dict(zip(worker_keys, worker_values))
            logging.info('adding {} values as name: {} ip: {} mac: {}'.format(worker_name, worker_name,
                                                                              worker_ip, worker_mac)) 
            self.inventory_dict['csah']['vars']['worker_nodes'].append(worker_node_dict_pairs)
            self.clear_screen()
        self.inventory_dict['csah']['vars']['number_of_workers'] = worker_nodes_count

    def dhcp_lease_times(self):
        """ 
        get dhcp lease times 
        
        """
        default_lease_time = input('enter a default lease time for dhcp\n'
                                   'default [800]: ')
        default = 800
        default_lease_time = set_values(default_lease_time, default, check='integer')
        max_lease_time = input('enter max lease time for dhcp\n'
                               'default [7200]: ')
        default = 7200
        max_lease_time = set_values(max_lease_time, default, check='integer')
        logging.info('adding default_lease_time: {} max_lease_time: {}'.format(default_lease_time,
                                                                               max_lease_time))
        self.inventory_dict['csah']['vars']['default_lease_time'] = default_lease_time
        self.inventory_dict['csah']['vars']['max_lease_time'] = max_lease_time

    def set_bond_network_details(self):
        """ 
        get bond details and user interfaces used for bond

        """
        self.clear_screen()
        default = 'bond0'
        name = input('enter bond name\n'
                     'default [bond0]: ')
        name = set_values(name, default)
        interfaces = input('enter bond interfaces seperated by \',\'\n'
                           'default [ens2f0,ens2f1]: ')
        default = 'ens2f0,ens2f1'
        interfaces = set_values(interfaces, default)
        default = 'mode=active-backup,miimon=100,primary=ens2f0'
        options = input('enter bond options \n'
                        'default [mode=active-backup,miimon=100,primary=ens2f0]: ')
        options = set_values(options, default)
        logging.info('adding bond_name: {} interfaces: {} bond_options: {}'.format(name, interfaces, options))
        self.inventory_dict['csah']['vars']['bond_name'] = name
        self.inventory_dict['csah']['vars']['bond_interfaces'] = interfaces
        self.inventory_dict['csah']['vars']['bond_options'] = options

    def get_dns_details(self):
        """ 
        get zone config file and cluster name used by DNS

        """
        self.clear_screen()
        zone_file = input('specify zone file \n'
                          'default [/var/named/ocp.zones]: ')
        default = '/var/named/ocp.zones'
        zone_file = set_values(zone_file, default)
        cluster_name = input('specify cluster name \n'
                             'default [ocp]: ')
        default = 'ocp'
        cluster_name = set_values(cluster_name, default)
        logging.info('adding zone_file: {} cluster: {}'.format(zone_file, cluster_name))
        self.inventory_dict['csah']['vars']['default_zone_file'] = zone_file
        self.inventory_dict['csah']['vars']['cluster'] = cluster_name

    def get_http_details(self):
        """ 
        get http details and directories names created under /var/www/html

        """
        self.clear_screen()
        port = input('enter http port \n'
                     'default [8080]: ')
        default = 8080
        port = set_values(port, default)
        port = validate_port(port)
        ignition_dir = input('specify dir where ignition files will be placed \n'
                             'directory will be created under /var/www/html \n'
                             'default [ignition]: ')
        default = 'ignition'
        ignition_dir = set_values(ignition_dir, default)
        ocp_version = input('specify the version of ocp \n'
                            'default [4.3]: ')
        default = 4.3
        ocp_version = set_values(ocp_version, default)
        logging.info('adding http_port: {} http_ignition: {} version: {}'.format(port, ignition_dir, ocp_version))
        self.inventory_dict['csah']['vars']['http_port'] = int(port)
        self.inventory_dict['csah']['vars']['os'] = 'rhcos'
        self.inventory_dict['csah']['vars']['http_ignition'] = ignition_dir
        self.inventory_dict['csah']['vars']['version'] = ocp_version

    def get_disk_name(self):
        """ 
        disknames used for each node type. 

        """
        self.clear_screen()
        default = 'nvme0n1'
        logging.info('ensure disknames are absolutely available. Otherwise OpenShift install fails')
        master_install_device = input('specify the master device that will be installed\n'
                                      'default [nvme0n1]: ')
        master_install_device = set_values(master_install_device, default)
        bootstrap_install_device = input('specify the bootstrap device that will be installed\n'
                                         'default [nvme0n1]: ')
        bootstrap_install_device = set_values(bootstrap_install_device, default)
        worker_install_device = input('specify the worker device that will be installed\n'
                                      'default [nvme0n1]: ')
        worker_install_device = set_values(worker_install_device, default)
        logging.info('adding master_install_device: {} bootstrap_install_device: {}\
                      worker_install_device: {}'.format(master_install_device, bootstrap_install_device,
                                                        worker_install_device))
        self.inventory_dict['csah']['vars']['master_install_device'] = master_install_device
        self.inventory_dict['csah']['vars']['bootstrap_install_device'] = bootstrap_install_device
        self.inventory_dict['csah']['vars']['worker_install_device'] = worker_install_device

    def set_haproxy(self):
        """ 
        sets default values for haproxy

        """
        logging.info('currently only haproxy is supported for load balancing')
        self.inventory_dict['csah']['vars']['proxy'] = 'haproxy'
        self.inventory_dict['csah']['vars']['haproxy_conf'] = '/etc/haproxy/haproxy.cfg'
        self.inventory_dict['csah']['vars']['master_ports'] = [{'port': 6443, 'description': 'apiserver'},
                                                               {'port': 22623 , 'description': 'configserver'}]
        self.inventory_dict['csah']['vars']['worker_ports'] = [{'port': 80, 'description': 'http'},
                                                               {'port': 443, 'description': 'https'}]

    def get_ignition_details(self):
        """ 
        get details from users used for install-config.yaml file

        """
        self.clear_screen()
        default = 'core'
        install_user = input('enter the user used to install openshift\n'
                             'DONOT CHANGE THIS VALUE\n'
                             'default [core]: ')
        install_user = set_values(install_user, default)
        default = 'openshift'
        install_dir = input('enter the directory where openshift installs\n'
                            'directory will be created under /home/core\n'
                            'default [openshift]: ')
        install_dir = set_values(install_dir, default)
        default = '10.128.0.0/14'
        pod_network_cidr = input('enter the pod network cidr\n'
                                 'default [10.128.0.0/14]: ')
        pod_network_cidr = set_values(pod_network_cidr, default)
        logging.info('pod network cidr: {}'.format(pod_network_cidr))
        pod_network_cidr = validate_network_cidr(pod_network_cidr)
        default = 23
        host_prefix = input('specify cidr notation for number of ips in each node: \n'
                            'cidr number should be an integer and less than 32\n'
                            'default [23]: ')
        host_prefix = set_values(host_prefix, default)
        host_prefix = validate_cidr(host_prefix)
        default = '172.30.0.0/16'
        service_network_cidr = input('specify the service network cidr\n'
                                     'default [172.30.0.0/16]: ')
        service_network_cidr = set_values(service_network_cidr, default)
        service_network_cidr = validate_network_cidr(service_network_cidr)
        logging.info('adding install_user: {} install_dir: {} cluster_network_cidr: {}\
                      host_prefix: {} service_network_cidr: {}'.format(install_user, install_dir,
                                                                pod_network_cidr, host_prefix, 
                                                                service_network_cidr))
        self.inventory_dict['csah']['vars']['install_user'] = install_user
        self.inventory_dict['csah']['vars']['install_dir'] = install_dir
        self.inventory_dict['csah']['vars']['cluster_network_cidr'] = pod_network_cidr
        self.inventory_dict['csah']['vars']['host_prefix'] = int(host_prefix)
        self.inventory_dict['csah']['vars']['service_network_cidr'] = service_network_cidr

    def yaml_inventory(self):
        """ 
        generate yaml file using user inputs
 
        """
        inventory_file = 'inventory_file'
        with open(inventory_file, 'w') as invfile:
            yaml.dump(self.inventory_dict, invfile, default_flow_style=False, sort_keys=False)

    def display_inventory(self):
        """ 
        display current user input details

        """
        logging.info(yaml.dump(self.inventory_dict, sort_keys=False, default_flow_style=False))
        input('Press Enter to continue ')

    def run(self):
        self.set_keys()
        self.set_haproxy()
        self.generate_inputs_menu()


def main():
    log_setup(log_file='inventory.log')
    logging.info('setting log file to inventory.log')
    gen_inv_file = InventoryFile()
    gen_inv_file.run()
    

if __name__ == "__main__":
    main()
