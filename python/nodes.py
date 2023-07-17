import logging
import base64

from helper import check_ip_ping, get_ip, get_user_response, set_values, validate_ip, \
                   get_idrac_creds, get_network_devices, get_server_model, map_interfaces_network, get_mac_address, \
                   get_network_device_mac, generate_network_devices_menu, get_device_enumeration, get_server_power_state



def get_worker_os():
    supported_os = ['rhel', 'rhcos']
    logging.info('supported OS include {}'.format(supported_os))
    os = input('enter the worker OS: ')
    while os not in supported_os:
        logging.error('Supported OS should be \'rhcos\' or \'rhel\'')
        os = input('enter the worker OS: ')

    return os


def set_network_details(node_type='', node_name='', ip='', mac='', bond_name='',
                        primary='', backup='', interfaces='', inventory='', os='', oob='', user='', passwd=''):
    """
    get bond details and user interfaces used for bond
    """
    devices = []
    node_keys = ['name', 'ip', 'mac', 'bond', 'primary', 'backup', 'options']
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

    if node_type == 'compute_nodes' and inventory['all']['vars']['install_type'] != 'IPI':
        node_keys = ['name', 'ip', 'mac', 'bond', 'primary', 'backup', 'options', 'interfaces', 'os']
        node_values.append(interfaces)
        node_values.append(os)
        logging.debug('adding interfaces in {} node: {}'.format(node_name, interfaces))

    if inventory['all']['vars']['install_type'] == 'IPI':
        node_keys = ['name', 'ip', 'mac', 'bond', 'primary', 'backup', 'options', 'oob', 'user', 'passwd']
        node_values.append(oob)
        node_values.append(user)
        node_values.append(base64.b64encode(passwd.encode('ascii')).decode())

    node_pairs = dict(zip(node_keys, node_values))
    logging.debug('node_values {} {} {}'.format(node_type, node_values, node_pairs))
    inventory['all']['vars'][node_type].append(node_pairs)

    return inventory

def get_nodes_info(node_type='', inventory='', add=False, idrac_user='', idrac_pass='', nodes_info=''):
    if add:
        nodes_count = len(nodes_info['new_compute_nodes'])
    else:
        nodes_count = len(nodes_info['control_nodes']) if node_type == 'control_nodes' else len(nodes_info['compute_nodes'])

    if inventory['all']['vars']['install_type'] == 'AI':
        bonding = 'No'
    else:
        bonding = input('Do you want to perform bonding for \'{}\' (y/No): '.format(node_type))
    
    valid_responses = ['y', 'No']
    while bonding not in valid_responses:
        logging.error('Invalid option provided. Enter \'y\' or \'No\'')
        bonding = input('Do you want to perform bonding (y/No): ')

    all_compute_nodes = ['compute_nodes', 'new_compute_nodes']

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
        #response = check_ip_ping(idrac_ip)

        #if node_type in all_compute_nodes:
        #    os = nodes_info[node_type][num]['os']
        #else:
        os = 'rhcos'

        #if response != 0:
        #    get_user_response(message='idrac ip {} not pingeable'.format(idrac_ip))
        #else:
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

        logging.info('\nselect network interfaces for node {}'.format(name))
        if map_devices:
            if bonding == 'y':
                show_menu = True
                if inventory['all']['vars']['install_type'] == 'UPI':
                    mac = get_network_device_mac(map_devices, user, passwd, base_api_url)
                    show_menu = False
                bond_name = 'bond0'
                active_bond_device = generate_network_devices_menu(map_devices, user, passwd, base_api_url, purpose='{} active bond interface'.format(name), show=show_menu)
                logging.debug('selected {} active bond interface: {}'.format(name, active_bond_device))
                active_bond_enumeration = get_device_enumeration(active_bond_device, os=os, server_model=server_model)
                logging.debug('{} active bond enumeration: {}'.format(name, active_bond_enumeration))
                pstate=''
                if inventory['all']['vars']['install_type'] == 'IPI':
                    mac = get_mac_address(active_bond_device, base_api_url, user, passwd)
                    #pstate = get_server_power_state(user, passwd, model_api_url)
                backup_bond_device = generate_network_devices_menu(map_devices, user, passwd, base_api_url, purpose='{} backup bond interface'.format(name), show=False)
                logging.debug('selected {} backup bond interface: {}'.format(name, backup_bond_device))
                backup_bond_enumeration = get_device_enumeration(backup_bond_device, os=os, server_model=server_model)
                #logging.debug('{} backup bond enumeration: {}'.format(name, backup_bond_enumeration))
                #logging.debug('interfaces: {}'.format(devices))
                #logging.debug('map interfaces: {}'.format(map_devices))

                if node_type in all_compute_nodes and os == 'rhel':
                    for device in map_devices:
                        interface_enumeration = get_device_enumeration(device, os=os, server_model=server_model)
                        interfaces_enumeration.append(interface_enumeration)
                else:
                    interfaces_enumeration.append(active_bond_enumeration)

                nodes = 'control_nodes' if node_type == 'control_nodes' else 'compute_nodes'
                inventory = set_network_details(node_type=nodes, node_name=name, ip=os_ip, mac=mac,
                                                bond_name=bond_name, primary=active_bond_enumeration,
                                                backup=backup_bond_enumeration, interfaces=interfaces_enumeration,
                                                inventory=inventory, os=os, oob=idrac_ip, user=user, passwd=passwd)

            else:
                nodes = 'control_nodes' if node_type == 'control_nodes' else 'compute_nodes'
                nic_device = generate_network_devices_menu(map_devices, user, passwd, base_api_url, purpose='{} nic port'.format(name))
                logging.debug('selected {} as nic port: {}'.format(name, nic_device))
                nic_device_enumeration = get_device_enumeration(nic_device, os=os, server_model=server_model)
                logging.debug('{} nic device enumeration: {}'.format(name, nic_device_enumeration))
                nic_mac = get_mac_address(nic_device, base_api_url, user, passwd)
                logging.debug('{} nic mac address: {}'.format(name, nic_mac))
                node_keys = ['name','ip','mac','interface','os']

                if node_type in all_compute_nodes and os == 'rhel':
                    node_keys = ['name','ip','mac','interface','os','interfaces']
                    for device in map_devices:
                        interface_enumeration = get_device_enumeration(device, os='rhel', server_model=server_model)
                        interfaces_enumeration.append(interface_enumeration)
                    node_values = [name, os_ip, nic_mac, nic_device_enumeration, os, interfaces_enumeration]
                else:
                    interfaces_enumeration.append(nic_device_enumeration)
                    node_values = [name, os_ip, nic_mac, nic_device_enumeration, os]

                if inventory['all']['vars']['install_type'] == 'IPI':
                    node_keys = ['name', 'ip', 'mac', 'interface', 'os', 'oob', 'user', 'passwd']
                    node_values = [name, os_ip, nic_mac, nic_device_enumeration, os, idrac_ip, user, base64.b64encode(passwd.encode('ascii')).decode()]

                logging.debug('{} node values: {}'.format(name, node_values))
                node_pairs = dict(zip(node_keys, node_values))
                inventory['all']['vars'][nodes].append(node_pairs)

    if node_type in all_compute_nodes and add:
        try:
            compute_nodes_count = inventory['all']['vars']['num_of_compute_nodes']
        except KeyError:
            inventory['all']['vars']['num_of_compute_nodes'] = 0
            compute_nodes_count = 0
        new_compute_nodes_count = compute_nodes_count + nodes_count
        inventory['all']['vars']['num_of_compute_nodes'] = new_compute_nodes_count

    return inventory

def get_nodes_disk_info(node_type='', add=False, inventory='', nodes_info=''):
    if add:
        nodes_count = len(nodes_info['new_compute_nodes'])
        if 'compute_nodes' in nodes_info:
            compute_count = len(nodes_info['compute_nodes'])
        else:
            compute_count = 0
        
        #for num in range(len(nodes_info['compute_nodes']),len(nodes_info['compute_nodes'])+len(nodes_info['new_compute_nodes'])):
        for num in range(compute_count,compute_count+len(nodes_info['new_compute_nodes'])):
            name=nodes_info[node_type][num-compute_count]['name']
            disk = input('\nEnter the installation disk name (Example - /dev/sda or /dev/nvme0n1) for \'{}\': '.format(name))
            #node_type='compute_nodes'
            inventory['all']['vars']['compute_nodes'][num]['installation_disk']=disk

    else:
        nodes_count = len(nodes_info['control_nodes']) if node_type == 'control_nodes' else len(nodes_info['compute_nodes'])

        for num in range(nodes_count):
            name=nodes_info[node_type][num]['name']
            disk = input('\nEnter the installation disk name (Example - /dev/sda or /dev/nvme0n1) for \'{}\': '.format(name))
            inventory['all']['vars'][node_type][num]['installation_disk']=disk
    return inventory

def get_sno_info(inventory='', idrac_user='', idrac_pass='', nodes_info=''):
    values = []
    devices = None
    map_devices = None
    interfaces_enumeration = []
    mac = ''
    node_type = 'control_nodes'
    name = nodes_info[node_type][0]['name']
    os_ip = nodes_info[node_type][0]['ip_os']
    os_ip = validate_ip(os_ip)
    idrac_ip = nodes_info[node_type][0]['ip_idrac']
    response = check_ip_ping(idrac_ip)
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

    logging.info('\nselect network interfaces for node {}'.format(name))
    if map_devices:
        mac = get_network_device_mac(map_devices, user, passwd, base_api_url)
    
    node_keys = ['name', 'ip', 'mac']
    node_values = []
    node_values = [name, os_ip, mac]
    node_pair = dict(zip(node_keys, node_values))
    inventory['all']['vars']['control_nodes'].append(node_pair)

    return inventory
