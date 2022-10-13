import argparse
import os
import logging
import socket
import sys
import yaml
import requests
import subprocess

from random import randint
from urllib.request import urlopen
from urllib.request import urlretrieve

from log_config import log_setup
from helper import create_dir, check_path, get_ip, get_network_device_mac, \
                   set_values, validate_cidr, validate_ip, validate_file, \
                   validate_network_cidr, validate_port, validate_url, \
                   check_user_input_if_integer, check_ip_ping, get_network_devices, \
                   map_interfaces_network, get_idrac_creds, generate_network_devices_menu, \
                   get_device_enumeration, get_user_response, get_mac_address

from nodes import get_nodes_info

class InventoryFile:
    def __init__(self, inventory_dict = {}, id_user='', id_pass='', version='', z_stream='', rhcos='', nodes_inventory=''):
        self.inventory_dict = inventory_dict
        self.id_user = id_user
        self.id_pass = id_pass
        self.version = str(version)

        if z_stream != 'latest':
            self.z_stream_release = self.version + '.' + z_stream
        else:
            self.z_stream_release = 'latest-{}'.format(self.version)
        if rhcos != 'latest':
            self.rhcos_release = self.version + '.' + rhcos
        else:
            self.rhcos_release = 'latest'
        self.nodes_inventory = nodes_inventory
        self.nodes_inv = ''
        self.software_dir = ''
        self.input_choice = ''
        self.cluster_install = 0
        self.ocp_client_base_url = 'https://mirror.openshift.com/pub/openshift-v4/clients/ocp/{}'.format(self.z_stream_release)
        self.ocp_urls = {'openshift_installer': '{}/openshift-install-linux.tar.gz'.format(self.ocp_client_base_url)}
        self.task_inputs = """
1: cluster info
2. dns
3: review inventory
4: generate inventory file
5: Exit
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
        self.inventory_dict['all'] = {'children': {}}
        self.inventory_dict['all']['vars'] = {}
        self.inventory_dict['all']['children'] = {'primary': {'hosts': '{}'.format(socket.getfqdn())}}


    def set_nodes_inventory(self):
        """ 
        read inventory file specifying bootstrap, control and compute nodes info

        """
        nodes_inventory_check = check_path(self.nodes_inventory, isfile=True)

        if nodes_inventory_check:
            with open(r'{}'.format(self.nodes_inventory)) as nodes_inv:
                self.nodes_inv = yaml.safe_load(nodes_inv)
        else:
            logging.error('incorrect nodes inventory specified: {}'.format(self.nodes_inventory))
            sys.exit()

    def generate_inputs_menu(self):
        """
        generates a menu of tasks for user input for each task
 
        """
        self.clear_screen()
        self.input_choice = ''
        valid_choices = range(1,10)
        while self.input_choice not in valid_choices:
             logging.info('{}'.format(self.task_inputs))
             try:
                 self.input_choice = int(input('task choice for necessary inputs: '))
                 if self.input_choice not in valid_choices:
                     logging.warn('Invalid choice. Valid choice is an integer from 1-9')
             except ValueError:
                 logging.error('Strings not a valid choice')

        logging.debug('user choice is {}'.format(self.input_choice))
        self.get_user_inputs_for_task()
            
    def get_user_inputs_for_task(self):
        """ 
        performs tasks based on user input

        """
        if self.input_choice == 5:
            sys.exit()
        elif self.input_choice == 1:
            self.get_cluster_nodes()
        elif self.input_choice == 2:
            self.get_dns_details()
        elif self.input_choice == 3:
            self.display_inventory()
        elif self.input_choice == 4:
            self.yaml_inventory(inventory_file='generated_inventory')
            sys.exit()
        self.generate_inputs_menu()

    def get_software_download_dir(self):
        """ 
        get software download directory to download OCP software bits
  
        """
        self.clear_screen()
        default = '/home/ansible/files'
        self.software_dir = input('provide complete path of directory to download OCP {} software bits\n'
                                  'default [/home/ansible/files]: '.format(self.version))
        self.software_dir = set_values(self.software_dir, default)
        dest_path_exist = check_path(self.software_dir, isdir=True)
        if dest_path_exist:
            logging.info('directory {} already exists'.format(self.software_dir))
        else:
            logging.info('Creating directory {}'.format(self.software_dir))
            create_dir(self.software_dir)

        self.inventory_dict['all']['vars']['software_src'] = self.software_dir

    def get_software(self):
        """ 
        performs OCP software bits download from the base urls
        specified in the class __init__ 
   
        """
        logging.info('downloading OCP {} software bits into {}'.format(self.software_dir, self.version))
        urlretrieve('{}/sha256sum.txt'.format(self.ocp_client_base_url),'{}/client.txt'.format(self.software_dir))
        shasum = False
        for url_key in self.ocp_urls.keys():
            url = self.ocp_urls[url_key]
            dest_name = url.split('/')[-1]
            dest_path = self.software_dir + '/' + dest_name
            dest_path_exist = check_path(dest_path, isfile=True)
            url_check = ''
            if dest_path_exist:
                logging.info('file {} already exists in {}'.format(dest_name, self.software_dir))
                self.inventory_dict['all']['vars'][url_key] = dest_name
            else:
                url_check = validate_url(url)
                if url_check == '':
                    logging.error('file {} in {} is not available'.format(dest_name, url_key))
                    self.inventory_dict['all']['vars'][url_key] = ''

            if not shasum:
                url_check = validate_url(url)
                if url_check == '':
                    logging.error('file {} in {} is not available'.format(dest_name, url_key))
                    self.inventory_dict['all']['vars'][url_key] = ''

            if url_check != '' and url_check.code == 200 and not shasum:
                logging.info('downloading {}'.format(dest_name))
                urlretrieve('{}'.format(url),'{}/{}'.format(self.software_dir, dest_name))
                self.inventory_dict['all']['vars'][url_key] = dest_name

    def get_untar_install_config(self):
        """
        it untar the openshift install config tar file
        """
        os.system('tar zxvf /home/ansible/files/openshift-install-linux.tar.gz -C /home/ansible/files/')
        os.system('chmod +x /home/ansible/files/openshift-install')
        url = subprocess.getoutput('/home/ansible/files/openshift-install coreos print-stream-json | grep location | grep x86_64 | grep iso | cut -d\\" -f4')
        print(url)
        response = requests.get(url)
        open("/home/ansible/files/rhcos-live.x86_64.iso", "wb").write(response.content)
        
    def get_cluster_nodes(self):
        self.get_sno_nodes()
                
    def get_sno_nodes(self):
        """ 
        get details about master node

        """
        self.clear_screen()
        self.inventory_dict['all']['vars']['sno_nodes'] = []
        self.inventory_dict = get_nodes_info(node_type='sno_nodes', inventory=self.inventory_dict, idrac_user=self.id_user, 
                                             idrac_pass=self.id_pass, nodes_info=self.nodes_inv)


    def dhcp_lease_times(self):
        """ 
        get dhcp lease times 
        
        """
        self.clear_screen()
        self.inventory_dict['all']['vars']['default_lease_time'] = 8000
        self.inventory_dict['all']['vars']['max_lease_time'] = 72000

    def get_dns_details(self):
        """ 
        get zone config file and cluster name used by DNS

        """
        self.clear_screen()
        response = input('specify a DNS forwarder if necessary (yes/No): ')
        accepted_response = ['yes', 'No']
        while response not in accepted_response:
            response = input('specify a DNS forwarder if necessary (yes/No): ')

        if response == 'yes':
            dns_forwarder = input('enter the DNS forwarder IP: ')
            self.inventory_dict['all']['vars']['dns_forwarder'] = dns_forwarder

        cluster_name = input('specify cluster name \n'
                             'default [ocp]: ')
        default = 'ocp'
        cluster_name = set_values(cluster_name, default)
        zone_file = input('specify zone file \n'
                          'default [/var/named/{}.zones]: '.format(cluster_name))
        default = '/var/named/{}.zones'.format(cluster_name)
        zone_file = set_values(zone_file, default)
        logging.info('adding zone_file: {} cluster: {}'.format(zone_file, cluster_name))
        self.inventory_dict['all']['vars']['default_zone_file'] = zone_file
        self.inventory_dict['all']['vars']['cluster'] = cluster_name

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
        logging.info('adding http_port: {} http_ignition: {} version: {}'.format(port, ignition_dir, self.version))
        self.inventory_dict['all']['vars']['http_port'] = int(port)
        self.inventory_dict['all']['vars']['os'] = 'rhcos'
        self.inventory_dict['all']['vars']['http_ignition'] = ignition_dir
        self.inventory_dict['all']['vars']['version'] = self.version

    def get_disk_name(self):
        """ 
        disknames used for each node type. 

        """
        self.clear_screen()
        default = 'nvme0n1'
        logging.info('ensure disknames are available. Otherwise OpenShift install fails')
        master_install_device = input('specify the control plane device that will be installed\n'
                                      'default [nvme0n1]: ')
        master_install_device = set_values(master_install_device, default)
        self.inventory_dict['all']['vars']['master_install_device'] = master_install_device
        if self.cluster_install == 1:
            pass
        else:
            worker_install_device = input('specify the compute node device that will be installed\n'
                                          'default [nvme0n1]: ')
            worker_install_device = set_values(worker_install_device, default)
            logging.info('adding master_install_device: {} worker_install_device: {}'.format(master_install_device, 
                          worker_install_device))
            self.inventory_dict['all']['vars']['worker_install_device'] = worker_install_device


    def get_ignition_details(self):
        """ 
        get details from users used for install-config.yaml file

        """
        self.clear_screen()
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
        logging.info('adding install_dir: {} cluster_network_cidr: {}\
                      host_prefix: {} service_network_cidr: {}'.format(install_dir,
                                                                pod_network_cidr, host_prefix, 
                                                                service_network_cidr))
        self.inventory_dict['all']['vars']['install_user'] = 'core'
        self.inventory_dict['all']['vars']['install_dir'] = install_dir
        self.inventory_dict['all']['vars']['cluster_network_cidr'] = pod_network_cidr
        self.inventory_dict['all']['vars']['host_prefix'] = int(host_prefix)
        self.inventory_dict['all']['vars']['service_network_cidr'] = service_network_cidr

    def yaml_inventory(self, inventory_file=''):
        """ 
        generate yaml file using user inputs
 
        """
        with open(inventory_file, 'w') as invfile:
            yaml.dump(self.inventory_dict, invfile, default_flow_style=False)

    def display_inventory(self):
        """ 
        display current user input details

        """
        self.clear_screen()
        logging.info(yaml.dump(self.inventory_dict, default_flow_style=False))
        input('Press Enter to continue ')

    def run(self):
        self.set_keys()
        self.dhcp_lease_times()
        self.set_nodes_inventory()
        self.generate_inputs_menu()


def main():
    parser = argparse.ArgumentParser(description="Generate Inventory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--run', help='generate inventory file', action='store_true', required=False)
    parser.add_argument('--release', type=str, help='specify OpenShift release version', required=True, choices=["4.10"], default=4.10)
    parser.add_argument('--z_stream', type=str, help='specify OpenShift z-stream version [DEVELOPMENT ONLY]', required=False, default='latest')
    parser.add_argument('--rhcos_ver', type=str, help='specify RHCOS version [DEVELOPMENT ONLY]', required=False, default='latest')
    parser.add_argument('--nodes', help='nodes inventory file', required=True)
    parser.add_argument('--id_user', help='specify idrac user', required=False)
    parser.add_argument('--id_pass', help='specify idrac user', required=False)
    parser.add_argument('--debug', help='specify debug logs', action='store_true', required=False)
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()
    args = parser.parse_args()
    log_setup(log_file='inventory.log', debug=args.debug)
    gen_inv_file = InventoryFile(id_user=args.id_user, id_pass=args.id_pass, version=args.release, z_stream=args.z_stream, rhcos=args.rhcos_ver, nodes_inventory=args.nodes)
    if args.run:
        gen_inv_file.run()
    
    if args.add:
        gen_inv_file.set_nodes_inventory()
        

if __name__ == "__main__":
    main()