import argparse
import os
import logging
import socket
import sys
import yaml
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

from nodes import get_nodes_info, get_sno_info
from nodes import get_nodes_disk_info

#subprocess.Popen('echo "Geeks 4 Geeks"', shell=True)

class InventoryFile:
    def __init__(self, inventory_dict = {}, id_user='', id_pass='', version='', z_stream='', rhcos='', nodes_inventory=''):
        self.inventory_dict = inventory_dict
        self.ansible = {}
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
        self.ocp_rhcos_base_url = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/{}/{}'.format(self.version, self.rhcos_release)
        self.ocp_urls = {'openshift_installer': '{}/openshift-install-linux.tar.gz'.format(self.ocp_client_base_url),
                         'openshift_client': '{}/openshift-client-linux.tar.gz'.format(self.ocp_client_base_url),
                         'initramfs': '{}/rhcos-live-initramfs.x86_64.img'.format(self.ocp_rhcos_base_url),
                         'kernel_file': '{}/rhcos-live-kernel-x86_64'.format(self.ocp_rhcos_base_url),
                         'uefi_file': '{}/rhcos-metal.x86_64.raw.gz'.format(self.ocp_rhcos_base_url),
                         'rootfs': '{}/rhcos-live-rootfs.x86_64.img'.format(self.ocp_rhcos_base_url)}
        self.task_inputs = """
 1: download OpenShift software
 2: cluster install
 3: infra components
 4: review inventory file
 5: generate inventory file
 6: exit
"""
        self.ipi_tasks = """
 1: cluster install
 2: infra components
 3: review inventory file
 4: generate inventory file
 5: exit
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
        self.clear_screen()
        self.ansible['roles'] = []
        self.inventory_dict['all'] = {'children': {}}
        self.inventory_dict['all']['vars'] = {}
        backup_management_node = input('Is there a backup management node [yes/No]: ')
        logging.debug('Is there a backup management node. user choice is {}'.format(backup_management_node))

        if backup_management_node == 'yes':
            backup_fqdn = input('Enter backup management node FQDN: ')
            self.inventory_dict['all']['children'] = {'primary': {'hosts': '{}'.format(socket.getfqdn())},
                                                      'secondary': {'hosts': '{}'.format(backup_fqdn)}}
            vip = input('Enter the VIP to be used for keepalived: ')
            self.inventory_dict['all']['vars']['vip'] = vip
        else:
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
        if self.install_type == 3:
            self.initiateAI()
            self.yaml_inventory(inventory_file='generated_inventory')
            sys.exit()
        else:
            self.input_choice = ''
            if self.install_type == 1:
                valid_choices = range(1,7)
                tasks = self.task_inputs
            elif self.install_type == 2:
                valid_choices = range(1,6)
                tasks = self.ipi_tasks
            while self.input_choice not in valid_choices:
                 logging.info('{}'.format(tasks))
                 try:
                     self.input_choice = int(input('task choice for necessary inputs: '))
                     if self.input_choice not in valid_choices:
                         logging.warn('Invalid choice. Valid choice is an integer from 1-6')
                 except ValueError:
                     logging.error('Strings not a valid choice')

            logging.debug('user choice is {}'.format(self.input_choice))
            self.get_user_inputs_for_task()
        #if self.install_type == 1:
        #    self.get_user_inputs_for_task()
        #elif self.install_type == 2:
        #    self.initiateIPI()
        #else:
        #    self.initiateAI()

    def get_user_inputs_for_task(self):
        """
        performs tasks based on user input

        """
        if self.install_type == 1:
            if self.input_choice == 1:
                self.get_software_download_dir()
                self.get_software()
            elif self.input_choice == 2:
                self.get_cluster_nodes()
            elif self.input_choice == 3:
                self.clear_screen()
                self.get_dns_details()
                self.get_fips_details()
                self.dhcp_lease_times()
                self.get_ntp_details()
                self.get_http_details()
                self.set_haproxy()
            elif self.input_choice == 4:
                self.display_inventory()
            elif self.input_choice == 5:
                self.yaml_inventory(inventory_file='generated_inventory')
                sys.exit()
            elif self.input_choice == 6:
                sys.exit()
        elif self.install_type == 2:
            if self.input_choice == 1:
                self.get_cluster_nodes()
            elif self.input_choice == 2:
                self.get_dns_details()
                self.get_fips_details()
            elif self.input_choice == 3:
                self.display_inventory()
            elif self.input_choice == 4:
                self.yaml_inventory(inventory_file='generated_inventory')
                sys.exit()
            elif self.input_choice == 5:
                sys.exit()
            
        self.generate_inputs_menu()

    def get_software_download_dir(self):
        """
        get software download directory to download OCP software bits

        """
        self.clear_screen()
        if self.cluster_install == 3:
            logging.info('option not applicable as Assisted Installer is used for SNO deployment.')
            input('Press any key to continue.')
            return
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
        
        logging.info('\nDownload may take few minutes depending on the network speed.\n')

        self.inventory_dict['all']['vars']['software_src'] = self.software_dir

    def get_software(self):
        """
        performs OCP software bits download from the base urls
        specified in the class __init__

        """
        if self.cluster_install == 3:
            return
        logging.info('\ndownloading OCP {} software bits into {}'.format(self.software_dir, self.version))
        urlretrieve('{}/sha256sum.txt'.format(self.ocp_client_base_url),'{}/client.txt'.format(self.software_dir))
        urlretrieve('{}/sha256sum.txt'.format(self.ocp_rhcos_base_url),'{}/rhcos.txt'.format(self.software_dir))
        shasum = False
        for url_key in self.ocp_urls.keys():
            url = self.ocp_urls[url_key]
            dest_name = url.split('/')[-1]
            dest_path = self.software_dir + '/' + dest_name
            dest_path_exist = check_path(dest_path, isfile=True)
            url_check = ''
            if dest_path_exist:
                logging.info('file {} already exists in {}'.format(dest_name, self.software_dir))
                shasum = validate_file(self.software_dir, dest_name, self.ocp_rhcos_base_url)
                self.inventory_dict['all']['vars'][url_key] = dest_name
                if shasum:
                    logging.info('Skipping downloading file {}.'.format(dest_name))
                    shasum = False
                    self.inventory_dict['all']['vars'][url_key] = dest_name
                    continue
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

        if not check_path(self.software_dir + '/pullsecret' , isfile=True):
            input('\n\n\nsave the pullsecret file under {} directory.\n'
                  'press any key to continue'.format(self.software_dir))

        self.inventory_dict['all']['vars']['pull_secret_file'] = 'pullsecret'

    def get_cluster_nodes(self):
        self.clear_screen()
        self.cluster_install = 0
        supported_install = """
 1. Standard - 5+ node (3 control and 2+ compute)
 2. Compact - 3 node (converged control/compute nodes)
        """
        logging.info('supported cluster install options: {}'.format(supported_install))
        valid_choices = [1, 2]
        while self.cluster_install not in valid_choices:
            try:
                self.cluster_install = int(input('enter cluster install option: '))
                logging.info('option selected: {}'.format(self.cluster_install))
            except ValueError:
                logging.error('valid choices are: {}'.format(valid_choices))

        if self.cluster_install == 3:
            self.inventory_dict['all']['vars']['cluster_install'] = '1 node'
            if len(self.nodes_inv['control_nodes']) != 1:
                logging.error('Single node is required, but {} is/are provided as input. Fix the issue and retry.'.format(len(self.nodes_inv['control_nodes'])))
                sys.exit(2)
            self.get_master_nodes()
        else:
            if len(self.nodes_inv['control_nodes']) != 3:
                logging.error('Three control nodes are required, but {} is/are provided as input. Fix the issue and retry.'.format(len(self.nodes_inv['control_nodes'])))
                sys.exit(2)
            else:
                if "control_nodes" not in self.nodes_inv:
                    logging.error('No control nodes specified. Fix the issue and retry.')
                    sys.exit(2)
                if self.cluster_install == 1 and "compute_nodes" not in self.nodes_inv:
                    logging.error('No compute nodes specified. Fix the issue and retry.')
                    sys.exit(2)
                logging.info('\nChecking iDRAC connectivity for control nodes.')
                for num in range(len(self.nodes_inv['control_nodes'])):
                    if check_ip_ping(self.nodes_inv['control_nodes'][num]['ip_idrac']) != 0:
                        logging.error('iDRAC IP for {} is not pingable. Fix the connectivity issue and retry.'.format(self.nodes_inv['control_nodes'][num]['name']))
                        sys.exit(2)
                    else:
                        logging.info('{} iDRAC is reachable.'.format(self.nodes_inv['control_nodes'][num]['name']))
            if self.cluster_install == 1:
                if len(self.nodes_inv['compute_nodes']) < 2:
                    logging.error('Atleast 2 compute nodes are required, but {} is/are provided as input. Fix the issue and retry.'.format(len(self.nodes_inv['compute_nodes'])))
                    sys.exit(2)
                else:
                    logging.info('Checking iDRAC connectivity for compute nodes.')
                    for num in range(len(self.nodes_inv['compute_nodes'])):
                        if check_ip_ping(self.nodes_inv['compute_nodes'][num]['ip_idrac']) != 0:
                            logging.error('iDRAC IP for {} is not pingable. Fix the connectivity issue and retry.'.format(self.nodes_inv['compute_nodes'][num]['name']))
                            sys.exit(2)
                        else:
                            logging.info('{} iDRAC is reachable.'.format(self.nodes_inv['compute_nodes'][num]['name']))

            input('press any key to continue')
            #self.get_install_options()

            # getting network info
            self.get_bootstrap_node()
            self.get_master_nodes()
            if self.cluster_install == 1:
                self.get_worker_nodes()
                self.inventory_dict['all']['vars']['cluster_install'] = '5+ node'
            else:
                self.inventory_dict['all']['vars']['cluster_install'] = '3 node'

            # getting disk info
            self.get_disk_name()

            # ignition config
            if self.install_type == 1:
                self.get_ignition_details()
            elif self.install_type == 2:
                self.get_ipi_ignition_details() 

    def get_install_options(self):
        """
        get details required for cluster installation

        """
        install_option = """
 1. network options
 2. disk options
 3. load balancer
 4. http
 5. ignition config
 6. return to main menu
        """
        option = ''
        self.clear_screen()
        logging.info('install options: {}'.format(install_option))
        valid_choices = range(1,7)
        while option not in valid_choices:
            try:
                option = int(input('enter install option: '))
                logging.info('option selected: {}'.format(option))
            except ValueError:
                logging.error('valid choices are: {}'.format(valid_choices)) 

        if option == 1:
            self.get_bootstrap_node()
            self.get_master_nodes()
            if self.cluster_install == 1:
                self.get_worker_nodes()
                self.inventory_dict['all']['vars']['cluster_install'] = '5+ node'
            else:
                self.inventory_dict['all']['vars']['cluster_install'] = '3 node'
        elif option == 2:
            self.get_disk_name()
        elif option == 3:
            self.set_haproxy()
        elif option == 4:
            self.get_http_details()
        elif option == 5:
            self.get_ignition_details()
        else:
            self.generate_inputs_menu() 
        self.get_install_options()

    def get_bootstrap_node(self):
        """
        get details about bootstrap node

        """
        bootstrap_mac = ''
        bootstrap_devices = None
        self.clear_screen()
        bootstrap_name = self.nodes_inv['bootstrap_kvm'][0]['name']
        bootstrap_os_ip = self.nodes_inv['bootstrap_kvm'][0]['ip_os']
        bootstrap_gw_ip = self.nodes_inv['bootstrap_kvm'][0]['ip_gw']
        if self.install_type == 1:
            bootstrap_mac = "52:54:00:{}:{}:{}".format(randint(10,99),randint(10,99),randint(10,99))
            logging.info('adding bootstrap_node values as name: {} ip: {} mac: {}'.format(bootstrap_name, bootstrap_os_ip,
                                                                                       bootstrap_mac))
            logging.info('If using an external DHCP server, add an IP reservation entry in the DHCP server.')
            input('press any key to continue')
            self.inventory_dict['all']['vars']['bootstrap_node'] = []
            bootstrap_keys = ['name','ip','mac']
            bootstrap_values = [bootstrap_name, bootstrap_os_ip, bootstrap_mac]
            bootstrap_pairs = dict(zip(bootstrap_keys, bootstrap_values))
            self.inventory_dict['all']['vars']['bootstrap_node'].append(bootstrap_pairs)
        elif self.install_type == 2:
            self.inventory_dict['all']['vars']['bootstrap_ip'] = bootstrap_os_ip
            self.inventory_dict['all']['vars']['bootstrap_gateway'] = bootstrap_gw_ip

    def get_master_nodes(self):
        """
        get details about master node

        """
        self.clear_screen()
        self.inventory_dict['all']['vars']['control_nodes'] = []
        self.inventory_dict['all']['vars']['num_of_control_nodes'] = len(self.nodes_inv['control_nodes'])
        if self.cluster_install == 3:
            self.inventory_dict = get_sno_info(inventory=self.inventory_dict, idrac_user=self.id_user,
                                             idrac_pass=self.id_pass, nodes_info=self.nodes_inv)
        else:
            self.inventory_dict = get_nodes_info(node_type='control_nodes', inventory=self.inventory_dict, idrac_user=self.id_user,
                                             idrac_pass=self.id_pass, nodes_info=self.nodes_inv)

    def get_worker_nodes(self):
        """
        get details about worker node

        """
        self.clear_screen()
        self.inventory_dict['all']['vars']['compute_nodes'] = []
        self.inventory_dict['all']['vars']['num_of_compute_nodes'] = len(self.nodes_inv['compute_nodes'])
        self.inventory_dict = get_nodes_info(node_type='compute_nodes', inventory=self.inventory_dict, idrac_user=self.id_user,
                                             idrac_pass=self.id_pass, nodes_info=self.nodes_inv)

    def add_new_worker_nodes(self):
        """
        get new worker nodes added to inventory file

        """
        self.clear_screen()
        current_inventory_file = input('\nEnter complete path to existing inventory file: ')
        file_exists = os.path.exists('{}'.format(current_inventory_file))
        if file_exists:
            with open('{}'.format(current_inventory_file), 'r') as file:
                 self.inventory_dict = yaml.safe_load(file)

            try:
                self.inventory_dict['all']['vars']['compute_nodes']
            except KeyError:
                logging.error('Inventory file does not contain worker nodes info')
                self.inventory_dict['all']['vars']['cluster_install'] = '5+ node'
                self.inventory_dict['all']['vars']['compute_nodes'] = []
                
                if self.cluster_install == 1:
                    self.get_compute_nodes_disk_info()
            self.inventory_dict = get_nodes_info(node_type='new_compute_nodes', inventory=self.inventory_dict, add=True,
                                                 idrac_user=self.id_user, idrac_pass=self.id_pass, nodes_info=self.nodes_inv)
            self.inventory_dict = get_nodes_disk_info(node_type='new_compute_nodes', add=True, inventory=self.inventory_dict, nodes_info=self.nodes_inv)
            #self.yaml_inventory(inventory_file=current_inventory_file)
            with open(current_inventory_file, 'w') as invfile:
                yaml.dump(self.inventory_dict, invfile, default_flow_style=False)
            
            sys.exit(2)
        else:
            logging.error('incorrect file path specified')
            sys.exit(2)

    def dhcp_lease_times(self):
        """
        get dhcp lease times

        """
        logging.info('\n\n')
        isDHCP = self.getInput(param='DHCP server')
        if isDHCP == 'No':
            self.inventory_dict['all']['vars']['dhcp'] = 'unmanaged'
            if 'dhcp' in self.ansible['roles']:
                self.ansible['roles'].remove('dhcp')
                self.inventory_dict['all']['vars'].pop('default_lease_time')
                self.inventory_dict['all']['vars'].pop('max_lease_time')
            return
        self.inventory_dict['all']['vars']['dhcp'] = 'managed'
        self.ansible['roles'].append('dhcp')
        #self.clear_screen()
        self.inventory_dict['all']['vars']['default_lease_time'] = 8000
        self.inventory_dict['all']['vars']['max_lease_time'] = 72000

    def get_dns_details(self):
        """
        get zone config file and cluster name used by DNS

        """
        logging.info('\n\n')
        #isDNS = input('Do you want to host DNS on CSAH (yes/No): ')
        #accepted_response = ['yes', 'No']
        #while isDNS not in accepted_response:
        #    response = input('Do you want to host DNS on CSAH (yes/No): ')

        isDNS = self.getInput(param='DNS')
        if isDNS == 'No':
            dns_ip = input('enter the DNS IP: ')
            cluster_name = input('specify cluster name \n'
                                 'default [ocp]: ')
            default = 'ocp'
            cluster_name = set_values(cluster_name, default)
            self.inventory_dict['all']['vars']['cluster'] = cluster_name
            self.inventory_dict['all']['vars']['dns_ip'] = dns_ip
            if 'dns' in self.ansible['roles']:
                self.ansible['roles'].remove('dns')
                self.inventory_dict['all']['vars'].pop('default_zone_file')
                self.inventory_dict['all']['vars'].pop('cluster')
                if 'dns_forwarder' in self.inventory_dict['all']['vars']:
                    self.inventory_dict['all']['vars'].pop('dns_forwarder')
            #self.ansible['roles'] = [self.ansible['roles'], 'dns']
            return

        self.ansible['roles'].append('dns')
        if 'dns_ip' in self.inventory_dict['all']['vars']:
            self.inventory_dict['all']['vars'].pop('dns_ip')
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
        
        if self.install_type == 3:
            api_ip = input('\nenter API virtual IP: ')
            logging.info('adding api_ip: {}'.format(api_ip))
        
            wildcard_ip = input('\nenter ingress virtual IP: ')
            logging.info('adding wildcard_ip: {}'.format(wildcard_ip))
        
            self.inventory_dict['all']['vars']['api_ip'] = api_ip
            self.inventory_dict['all']['vars']['wildcard_ip'] = wildcard_ip

    def get_fips_details(self):
        """
        get FIPS details

        """
        logging.info('\n\n')
        isFIPS = self.getInput(param='FIPS')
        if isFIPS == 'No' and self.install_type == 3:
            return

        if isFIPS == 'No':
            self.inventory_dict['all']['vars']['fips'] = 'false'
        else:
            self.inventory_dict['all']['vars']['fips'] = 'true'

    
    
    def get_ntp_details(self):
        """
        get NTP details

        """
        logging.info('\n\n')
        isNTP = self.getInput(param='NTP')
        if isNTP == 'No' and self.install_type == 3:
            return

        if isNTP == 'No':
            self.inventory_dict['all']['vars']['ntp'] = 'unmanaged'
            self.inventory_dict['all']['vars']['ntp_ip'] = input('enter NTP IP : ')
        else:
            self.inventory_dict['all']['vars']['ntp'] = 'managed'

    def get_http_details(self):
        """
        get http details and directories names created under /var/www/html

        """
        logging.info('\n\n')
        if self.cluster_install == 3:
            #input('option not applicable for single node deployment.\n'
            #             'Press any key to continue.')
            return
        isHTTP = self.getInput(param='HTTP server')

        if isHTTP == 'No':
            logging.info('Ensure the nodes have connectivity to the HTTP server.')
            self.inventory_dict['all']['vars']['http'] = 'unmanaged'
            self.inventory_dict['all']['vars']['http_ip'] = input('enter HTTP server IP : ')
        else:
            self.inventory_dict['all']['vars']['http'] = 'managed'
            self.ansible['roles'].append('http')
        port = input('enter http port \n'
                     'default [8080]: ')
        default = 8080
        port = set_values(port, default)
        port = validate_port(port)
        if isHTTP == 'No':
            msg = 'specify http server dir where ignition files will be placed : '
        else:
            msg = """specify dir where ignition files will be placed \ndirectory will be created under /var/www/html \ndefault [ignition]: """
        ignition_dir = input(msg)
        default = 'ignition'
        ignition_dir = set_values(ignition_dir, default)
        if isHTTP == 'No':
            logging.info('Copy the files from {} directory to the HTTP server.'.format(ignition_dir))
        logging.info('adding http_port: {} http_ignition: {} version: {}'.format(port, ignition_dir, self.version))
        self.inventory_dict['all']['vars']['http_port'] = int(port)
        self.inventory_dict['all']['vars']['os'] = 'rhcos'
        self.inventory_dict['all']['vars']['http_ignition'] = ignition_dir
        self.inventory_dict['all']['vars']['version'] = self.version

    def get_disk_name(self):
        self.get_master_nodes_disk_info()
        if self.cluster_install == 1:
            self.get_compute_nodes_disk_info()

    def get_master_nodes_disk_info(self):
        
	#disknames used for each master node.

        #self.inventory_dict = get_nodes_disk_info(node_type='control_nodes', inventory=self.inventory_dict, nodes_info=self.nodes_inv)

        self.clear_screen()
        default = '/dev/nvme0n1'
        logging.info('ensure disknames are available. Otherwise OpenShift install fails')
        master_install_device = input('\nEnter the installation disk name (Example - /dev/sda or /dev/nvme0n1) for control plane nodes\n'
                                      'default [/dev/nvme0n1]: ')
        master_install_device = set_values(master_install_device, default)
        self.inventory_dict['all']['vars']['master_install_device'] = master_install_device


    def get_compute_nodes_disk_info(self):
        
        #disknames used for each compute node.

        self.inventory_dict = get_nodes_disk_info(node_type='compute_nodes', inventory=self.inventory_dict, nodes_info=self.nodes_inv)


    def set_haproxy(self):
        """
        sets default values for haproxy

        """
        #self.clear_screen()
        logging.info('\n\n')
        if self.cluster_install == 3:
            #input('option not applicable for single node deployment.\n'
            #             'Press any key to continue.')
            return
        #logging.info('currently only haproxy is supported as load balancer on CSAH')
        installLB = self.getInput(param='HAProxy Load Balancer')

        if installLB == 'No':
            self.inventory_dict['all']['vars']['proxy'] = 'lb'
            self.inventory_dict['all']['vars']['lb_vip'] = input('enter the virtual ip of external Load Balancer : ')
            return

        self.ansible['roles'].append('proxy')
        self.inventory_dict['all']['vars']['proxy'] = 'haproxy'
        self.inventory_dict['all']['vars']['haproxy_conf'] = '/etc/haproxy/haproxy.cfg'
        self.inventory_dict['all']['vars']['master_ports'] = [{'port': 6443, 'description': 'apiserver'},
                                                              {'port': 22623 , 'description': 'configserver'}]
        self.inventory_dict['all']['vars']['worker_ports'] = [{'port': 80, 'description': 'http'},
                                                              {'port': 443, 'description': 'https'}]

    def get_ignition_details(self):
        """
        get details from users used for install-config.yaml file

        """
        self.clear_screen()
        if self.cluster_install == 3:
            input('option not applicable for single node deployment.\n'
                         'Press any key to continue.')
            return
        self.ansible['roles'].append('ignition')
        default = 'openshift'
        install_dir = input('enter the directory where openshift installs\n'
                            'directory will be created under /home/core\n'
                            'default [openshift]: ')
        install_dir = set_values(install_dir, default)
        network_type = input('enter the network type (OVNKubernetes / OpenShiftSDN) : ')
        networkType = ['OVNKubernetes', 'OpenShiftSDN']
        while network_type not in networkType:
            network_type = input('enter the network type (OVNKubernetes / OpenShiftSDN) : ')

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
        self.inventory_dict['all']['vars']['network_type'] = network_type

    def get_ipi_ignition_details(self):
        """
        get details from users used for install-config.yaml file

        """
        version = 'latest-{}'.format(self.version)
        self.inventory_dict['all']['vars']['compute_nodes'] = []
        try:
            self.inventory_dict['all']['vars']['num_of_compute_nodes'] = len(self.nodes_inv['compute_nodes'])
        except KeyError:
            self.inventory_dict['all']['vars']['num_of_compute_nodes'] = 0
        network_type = input('\nenter the network type (OVNKubernetes / OpenShiftSDN) : ')
        networkType = ['OVNKubernetes', 'OpenShiftSDN']
        while network_type not in networkType:
            network_type = input('enter the network type (OVNKubernetes / OpenShiftSDN) : ')
        
        machine_network_cidr = input('\nspecify the network cidr of the external network (format x.x.x.x/x): ')
        machine_network_cidr = validate_network_cidr(machine_network_cidr)
        logging.info('adding machine_network_cidr: {}'.format(machine_network_cidr))
        
        api_ip = input('\nenter API virtual IP: ')
        logging.info('adding api_ip: {}'.format(api_ip))
        
        wildcard_ip = input('\nenter ingress virtual IP: ')
        logging.info('adding wildcard_ip: {}'.format(wildcard_ip))
       
        default = '/home/ansible/files/pullsecret' 
        pull_secret_file = input('\nenter pullsecret file location\n'
                                 'default [/home/ansible/files/pullsecret]: ')
        pull_secret_file = set_values(pull_secret_file, default)
        logging.info('adding pull_secret_file: {}'.format(pull_secret_file))
        
        self.inventory_dict['all']['vars']['machine_network_cidr'] = machine_network_cidr
        self.inventory_dict['all']['vars']['network_type'] = network_type
        self.inventory_dict['all']['vars']['api_ip'] = api_ip
        self.inventory_dict['all']['vars']['wildcard_ip'] = wildcard_ip
        self.inventory_dict['all']['vars']['pull_secret_file'] = pull_secret_file
        self.inventory_dict['all']['vars']['version'] = version
        self.ansible['roles'].append('ipi')

    def yaml_inventory(self, inventory_file=''):
        """
        generate yaml file using user inputs

        """
        with open(inventory_file, 'w') as invfile:
            yaml.dump(self.inventory_dict, invfile, default_flow_style=False)
        if self.inventory_dict['all']['vars']['install_type'] == "UPI":
            self.ansible['roles'].append('keepalived')
            if self.cluster_install != 3:
                self.ansible['roles'].append('pxe')
                self.ansible['roles'].append('bootstrap')
        if 'secondary' in self.inventory_dict['all']['children']:
            self.ansible['roles']
            secondaryAnsible = self.ansible['roles'][:]
            if 'dhcp' in secondaryAnsible:
                secondaryAnsible.remove('dhcp')
            if 'bootstrap' in secondaryAnsible:
                secondaryAnsible.remove('bootstrap')
            a = [{'hosts': 'primary', 'become': "yes", 'roles': [*set(self.ansible['roles'])]},
                 {'hosts': 'secondary', 'become': 'yes', 'roles': [*set(secondaryAnsible)]}]
        else:
            a = [{'hosts': 'primary', 'become': "yes", 'roles': [*set(self.ansible['roles'])]}]
        with open('ansible.yaml', 'w') as asbfile:
            yaml.dump(a, asbfile, Dumper=self.Dumper, default_flow_style=False)

    class Dumper(yaml.Dumper):
        def increase_indent(self, flow=False, *args, **kwargs):
            return super().increase_indent(flow=flow, indentless=False)

    def display_inventory(self):
        """
        display current user input details

        """
        self.clear_screen()
        logging.info(yaml.dump(self.inventory_dict, default_flow_style=False))
        logging.info('\n')
        if self.install_type == 1:
            if self.cluster_install != 3:
                self.ansible['roles'].append('pxe')
                self.ansible['roles'].append('bootstrap')
        if 'secondary' in self.inventory_dict['all']['children']:
            secondaryAnsible = self.ansible['roles'][:]
            if 'dhcp' in secondaryAnsible:
                secondaryAnsible.remove('dhcp')
            if 'bootstrap' in secondaryAnsible:
                secondaryAnsible.remove('bootstrap')
            a = [{'hosts': 'primary', 'become': "yes", 'roles': [*set(self.ansible['roles'])]},
                 {'hosts': 'secondary', 'become': 'yes', 'roles': [*set(secondaryAnsible)]}]
        else:
            a = [{'hosts': 'primary', 'become': "yes", 'roles': [*set(self.ansible['roles'])]}]
        logging.info(yaml.dump(a, Dumper=self.Dumper, default_flow_style=False))
        input('Press Enter to continue ')

    def run(self):
        self.set_keys()
        #self.set_haproxy()
        #self.dhcp_lease_times()
        self.set_nodes_inventory()
        self.getInstallationType()
        #self.generate_inputs_menu()

    def getInput(self, param):
        """
        helper function to fetch input from user

        """
        msg = 'Do you want to install ' + param + ' on CSAH '
        response = input(msg + '[yes/No]: ')
        accepted_response = ['yes', 'No']
        while response not in accepted_response:
            #response = input('Do you want to install ' + param + ' on CSAH [yes/No]: ')
            response = input(msg + '[yes/No]: ')

        return response

    def getInstallationType(self):
        """
        function to get the type of installation: UPI, IPI or Assisted INstaller
        """
        install_type = """
 1. UPI
 2. IPI
 3. Assisted Installer
        """
        option = ''
        self.clear_screen()
        logging.info('installation type: {}'.format(install_type))
        valid_choices = range(1,4)
        while option not in valid_choices:
            try:
                option = int(input('enter install type: '))
                self.install_type = option
                logging.info('option selected: {}'.format(option))
            except ValueError:
                logging.error('valid choices are: {}'.format(valid_choices))
        
        if self.install_type == 1:
            self.inventory_dict['all']['vars']['install_type'] = 'UPI'
        elif self.install_type == 2:
            self.inventory_dict['all']['vars']['install_type'] = 'IPI'
        else:
            self.inventory_dict['all']['vars']['install_type'] = 'AI'
        self.generate_inputs_menu()

    def initiateAI(self):
        """
        function to get information required for Assisted Installer install
        DNS, DHCP are the valid scenarios
        """
        self.get_dns_details()
        self.dhcp_lease_times()
        #self.get_ntp_details()
        self.yaml_inventory(inventory_file='generated_inventory')
        
        if 'dns' in self.ansible['roles'] or 'dhcp' in self.ansible['roles']:
            if "control_nodes" not in self.nodes_inv or len(self.nodes_inv['control_nodes']) < 1:
                logging.error('No control nodes specified. Fix the issue and retry.')
                sys.exit(2)
            if len(self.nodes_inv['control_nodes']) == 1:
                self.inventory_dict['all']['vars']['cluster_install'] = '1 node'
            elif len(self.nodes_inv['control_nodes']) == 3 and "compute_nodes" not in self.nodes_inv:
                self.inventory_dict['all']['vars']['cluster_install'] = '3 node'
            else:
                self.inventory_dict['all']['vars']['cluster_install'] = '5+ node'
            for node in ['control_nodes', 'compute_nodes']:
                if node not in self.nodes_inv or len(self.nodes_inv[node]) < 1:
                    continue
                self.inventory_dict['all']['vars'][node] = []
                self.inventory_dict['all']['vars']['num_of_' + node] = len(self.nodes_inv[node])
                if 'dhcp' not in self.ansible['roles']:
                    for num in range(len(self.nodes_inv[node])):
                        name = self.nodes_inv[node][num]['name']
                        os_ip = self.nodes_inv[node][num]['ip_os']
                        os_ip = validate_ip(os_ip)
                        node_keys = ['name','ip']
                        node_values = [name, os_ip]
                        logging.debug('{} node values: {}'.format(name, node_values))
                        node_pairs = dict(zip(node_keys, node_values))
                        self.inventory_dict['all']['vars'][node].append(node_pairs)
                else:
                    self.inventory_dict = get_nodes_info(node_type=node, inventory=self.inventory_dict, idrac_user=self.id_user,
                                                        idrac_pass=self.id_pass, nodes_info=self.nodes_inv)
            #if "compute_nodes" in self.nodes_inv:
            #    self.inventory_dict['all']['vars']['compute_nodes'] = []
            #    self.inventory_dict['all']['vars']['num_of_compute_nodes'] = len(self.nodes_inv['compute_nodes'])
            #    self.inventory_dict = get_nodes_info(node_type='compute_nodes', inventory=self.inventory_dict, idrac_user=self.id_user,
            #                                         idrac_pass=self.id_pass, nodes_info=self.nodes_inv)

def main():
    parser = argparse.ArgumentParser(description="Generate Inventory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--run', help='generate inventory file', action='store_true', required=False)
    group.add_argument('--add', help='number of worker nodes', action='store_true', required=False)
    parser.add_argument('--release', type=str, help='specify OpenShift release version', required=False, choices=["4.10", "4.11", "4.14"], default="4.14")
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
        gen_inv_file.add_new_worker_nodes()


if __name__ == "__main__":
    main()

