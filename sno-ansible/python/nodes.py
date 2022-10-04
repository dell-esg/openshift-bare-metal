import logging

from helper import check_ip_ping, get_ip, get_user_response, set_values, validate_ip, \
                   get_idrac_creds, get_network_devices, get_server_model, map_interfaces_network, get_mac_address, \
                   get_network_device_mac, generate_network_devices_menu, get_device_enumeration


def set_network_details(node_type='' , node_name='', ip='', mac='', bond_name='',
                        primary='', backup='', inventory=''):
    """
    get bond details and user interfaces used for bond
    """
    devices = []
    node_keys = ['name', 'ip', 'mac', 'bond', 'primary', 'backup', 'options']
    node_type =  'sno_nodes' 
    node_values = []
    bond_options = 'mode=active-backup'
    bond_interfaces = '{},{}'.format(primary, backup)
    node_values.append(node_name)
    node_values.append(ip)
    node_values.append(mac)
    node_values.append(bond_name)
    node_values.append(primary)
    node_values.append(backup)
    node_values.append(bond_options)
    
    node_pairs = dict(zip(node_keys, node_values))
    logging.debug('node_values {} {} {}'.format(node_type, node_values, node_pairs))
    inventory['all']['vars'][node_type].append(node_pairs)
    return inventory

def get_nodes_info(node_type='', inventory='', add=False, idrac_user='', idrac_pass='', nodes_info=''):
    bonding = input('Do you want to perform bonding for \'{}\' (y/NO): '.format(node_type))
    valid_responses = ['y', 'NO']
    nodes_count= len(nodes_info['sno_nodes'])

    while bonding not in valid_responses:
        logging.error('Invalid option provided. Enter \'y\' or \'NO\'')
        bonding = input('Do you want to perform bonding (y/NO): ')

    for num in range(nodes_count):
        values = []
        devices = None
        map_devices = None
        interfaces_enumeration = []
        mac = ''
        name = nodes_info[node_type][num]['name']
        os_ip = nodes_info[node_type][num]['ip_os']
        os_ip = validate_ip(os_ip)
        idrac_ip = nodes_info[node_type][num]['ip_idrac']
        response = check_ip_ping(idrac_ip)
        os = 'rhcos'
        nodes = 'sno_nodes'
        node_type = 'sno_nodes'
        if response != 0:
            get_user_response(message='idrac ip {} not pingeable'.format(idrac_ip))
        else:
            if idrac_user and idrac_pass:
                user, passwd = idrac_user, idrac_pass
            else:
                user, passwd = get_idrac_creds(idrac_ip)

            base_api_url = 'https://{}/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces'.format(idrac_ip)
            model_api_url = 'https://{}/redfish/v1/Systems/System.Embedded.1'.format(idrac_ip)
            server_model = get_server_model(user, passwd, model_api_url)
            devices = get_network_devices(user, passwd, base_api_url)

        if devices:
            map_devices = map_interfaces_network(devices)

        logging.info('select network interfaces for node {}'.format(name))
        if map_devices:
            if bonding == 'y':
                mac = get_network_device_mac(map_devices, user, passwd, base_api_url)
                bond_name = 'bond0'
                active_bond_device = generate_network_devices_menu(map_devices, purpose='{} active bond interface'.format(name))
                logging.debug('selected {} active bond interface: {}'.format(name, active_bond_device))
                active_bond_enumeration = get_device_enumeration(active_bond_device, os=os, server_model=server_model)
                logging.debug('{} active bond enumeration: {}'.format(name, active_bond_enumeration))
                backup_bond_device = generate_network_devices_menu(map_devices, purpose='{} backup bond interface'.format(name))
                logging.debug('selected {} backup bond interface: {}'.format(name, backup_bond_device))
                backup_bond_enumeration = get_device_enumeration(backup_bond_device, os=os, server_model=server_model)
                logging.debug('{} backup bond enumeration: {}'.format(name, backup_bond_enumeration))
                logging.debug('interfaces: {}'.format(devices))
                logging.debug('map interfaces: {}'.format(map_devices))
                interfaces_enumeration.append(active_bond_enumeration)
                inventory = set_network_details(node_type=nodes, node_name=name, ip=os_ip, mac=mac,
                                                bond_name=bond_name, primary=active_bond_enumeration,
                                                backup=backup_bond_enumeration, inventory=inventory )

            else:
                nic_device = generate_network_devices_menu(map_devices, purpose='{} nic port'.format(name))
                logging.debug('selected {} as nic port: {}'.format(name, nic_device))
                nic_device_enumeration = get_device_enumeration(nic_device, os=os, server_model=server_model)
                logging.debug('{} nic device enumeration: {}'.format(name, nic_device_enumeration))
                nic_mac = get_mac_address(nic_device, base_api_url, user, passwd)
                logging.debug('{} nic mac address: {}'.format(name, nic_mac))
                node_keys = ['name','ip','mac','interface','os']

                logging.debug('{} node values: {}'.format(name, node_values))
                node_pairs = dict(zip(node_keys, node_values))
                inventory['all']['vars'][nodes].append(node_pairs)

    return inventory

