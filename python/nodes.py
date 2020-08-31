import logging

from helper import check_ip_ping, get_ip, get_user_response, set_values, validate_ip, \
                   get_idrac_creds, get_network_devices, map_interfaces_network, get_mac_address, \
                   get_network_device_mac, generate_network_devices_menu, get_device_enumeration
                   


def get_worker_os():
    supported_os = ['rhel', 'rhcos']
    logging.info('supported OS include {}'.format(supported_os))
    os = input('enter the worker OS: ')
    while os not in supported_os:
        logging.error('Supported OS should be \'rhcos\' or \'rhel\'')
        os = input('enter the worker OS: ')

    return os


def set_network_details(node_type='', node_name='', ip='', mac='', bond_name='', 
                        primary='', backup='', interfaces='', inventory='', os=''):
    """ 
    get bond details and user interfaces used for bond
    """
    devices = []
    node_keys = ['name', 'ip', 'mac', 'bond', 'primary', 'backup', 'options']
    node_values = []
    bond_options = 'lacp_rate=1,miimon=100,mode=802.3ad,xmit_hash_policy=layer3+4'
    bond_interfaces = '{},{}'.format(primary, backup)
    node_values.append(node_name)
    node_values.append(ip)
    node_values.append(mac)
    node_values.append(bond_name)
    node_values.append(primary)
    node_values.append(backup)
    node_values.append(bond_options)

    if node_type == 'worker_nodes':
        node_keys = ['name', 'ip', 'mac', 'bond', 'primary', 'backup', 'options', 'interfaces', 'os']
        node_values.append(interfaces)
        node_values.append(os)
        logging.debug('adding interfaces in {} node: {}'.format(node_name, interfaces))

    node_pairs = dict(zip(node_keys, node_values))
    logging.debug('node_values {} {} {}'.format(node_type, node_values, node_pairs))
    inventory['csah']['vars'][node_type].append(node_pairs)

    return inventory

def get_nodes_info(node_type='master', inventory='', add=False, idrac_user='', idrac_pass=''):
    desc = 'enter number of new worker nodes' if add else 'enter number of {} nodes'.format(node_type)
    nodes_count = input('{}\n'
                        'default [3]: '.format(desc))
    default = 3
    nodes_count = set_values(nodes_count, default, check='integer')

    if not add:
        inventory['csah']['vars']['{}_nodes'.format(node_type)] = []

    bonding = input('Do you want to perform bonding (y/NO): ')
    valid_responses = ['y', 'NO']

    while bonding not in valid_responses:
        logging.error('Invalid option provided. Enter \'y\' or \'NO\'')
        bonding = input('Do you want to perform bonding (y/NO): ')

    for num in range(nodes_count):
        values = []
        devices = None
        map_devices = None
        interfaces_enumeration = []
        mac = ''
        
        if node_type == 'master':
            default = 'etcd-{}'.format(num)
        else:
            default = '{}-{}'.format(node_type, num)
   
        if add:
            default = 'new-{}-{}'.format(node_type, num)
 
        name = input('enter the {} {} node name \n'
                     'default [{}]: '.format(node_type, num, default))
        name = set_values(name, default)

        if node_type == 'worker':
            default = 'rhcos'
            os = get_worker_os()
            os = set_values(os, default)            
        else:
            os = 'rhcos'

        os_ip = get_ip(node_name=name, ip_type='os')
        os_ip = validate_ip(os_ip)
        idrac_ip = get_ip(node_name=name, ip_type='idrac')
        response = check_ip_ping(idrac_ip)
            
        if response != 0:
            get_user_response(message='idrac ip {} not pingeable'.format(idrac_ip))
        else:
            if idrac_user and idrac_pass:
                user, passwd = idrac_user, idrac_pass
            else:
                user, passwd = get_idrac_creds(idrac_ip)

            base_api_url = 'https://{}/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces'.format(idrac_ip)
            devices = get_network_devices(user, passwd, base_api_url)
        
        if devices:
            map_devices = map_interfaces_network(devices)

        if map_devices:
            if bonding == 'y':
                mac = get_network_device_mac(map_devices, user, passwd, base_api_url)
                bond_name = 'bond0'
                active_bond_device = generate_network_devices_menu(map_devices, purpose='{} active bond interface'.format(name))
                logging.debug('selected {} active bond interface: {}'.format(name, active_bond_device))
                active_bond_enumeration = get_device_enumeration(active_bond_device, os=os)
                logging.debug('{} active bond enumeration: {}'.format(name, active_bond_enumeration))
                backup_bond_device = generate_network_devices_menu(map_devices, purpose='{} backup bond interface'.format(name))
                logging.debug('selected {} backup bond interface: {}'.format(name, backup_bond_device))
                backup_bond_enumeration = get_device_enumeration(backup_bond_device, os=os)
                logging.debug('{} backup bond enumeration: {}'.format(name, backup_bond_enumeration))
                logging.debug('interfaces: {}'.format(devices))
                logging.debug('map interfaces: {}'.format(map_devices))
                    
                if node_type == 'worker' and os == 'rhel':
                    for device in map_devices:
                        interface_enumeration = get_device_enumeration(device, os=os)
                        interfaces_enumeration.append(interface_enumeration)
                else:
                    interfaces_enumeration.append(active_bond_enumeration)
                
                inventory = set_network_details(node_type='{}_nodes'.format(node_type), node_name=name, 
                                                ip=os_ip, mac=mac, bond_name=bond_name, primary=active_bond_enumeration,
                                                backup=backup_bond_enumeration, interfaces=interfaces_enumeration,
                                                inventory=inventory, os=os)
                
            else:
                nic_device = generate_network_devices_menu(map_devices, purpose='{} nic port'.format(name))
                logging.debug('selected {} as nic port: {}'.format(name, nic_device))
                nic_device_enumeration = get_device_enumeration(nic_device, os=os)
                logging.debug('{} nic device enumeration: {}'.format(name, nic_device_enumeration))
                nic_mac = get_mac_address(nic_device, base_api_url, user, passwd)
                logging.debug('{} nic mac address: {}'.format(name, nic_mac))
                node_keys = ['name','ip','mac','interface','os']

                if node_type == 'worker' and os == 'rhel':
                    node_keys = ['name','ip','mac','interface','os','interfaces']
                    for device in map_devices:
                        interface_enumeration = get_device_enumeration(device, os='rhel')
                        interfaces_enumeration.append(interface_enumeration)
                    node_values = [name, os_ip, nic_mac, nic_device_enumeration, os, interfaces_enumeration]
                else:
                    interfaces_enumeration.append(nic_device_enumeration) 
                    node_values = [name, os_ip, nic_mac, nic_device_enumeration, os]

                logging.debug('{} node values: {}'.format(name, node_values))
                node_pairs = dict(zip(node_keys, node_values))
                inventory['csah']['vars']['{}_nodes'.format(node_type)].append(node_pairs)

    if node_type == 'worker' and add:
        worker_nodes_count = inventory['csah']['vars']['number_of_workers']
        new_worker_nodes_count = worker_nodes_count + nodes_count
        inventory['csah']['vars']['number_of_workers'] = new_worker_nodes_count
    elif node_type == 'worker' and not add:
        inventory['csah']['vars']['number_of_workers'] = nodes_count
    else:
        inventory['csah']['vars']['number_of_masters'] = nodes_count

    return inventory
