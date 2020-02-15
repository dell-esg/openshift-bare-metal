import ipaddress
import json
import os
import re
import requests
import sys

from urllib.request import urlopen
from urllib3.exceptions import InsecureRequestWarning


def create_dir(directory):
    try:
        os.makedirs(directory)
        print('successfully created directory {}'.format(directory))
    except OSError:
        print('creating directory {} failed'.format(directory))

def check_path(path, isfile=False, isdir=False):
    
    return os.path.isfile(path) if isfile else os.path.isdir(path)

def set_values(user_input, default):
    
    return default if not user_input else user_input

def validate_url(url):
    
    url_verify = urlopen(url)

    return True if url_verify.code == 200 else False

def get_ip(node_type='', ip_type=''):
    
    ip = ''
    while True:
        ip = input('ip address for {} in {} node: '.format(ip_type, node_type))
        ip_check = validate_ip(ip)
        if ip_check:
            break
        else:
            print('ip address should be in format: x.x.x.x')
    
    return ip  

def get_mac(node_type=''):

    mac=''
    while True:
        mac = input('mac address for {} node: '.format(node_type))
        mac_check = validate_mac(mac)
        if mac_check:
            break
        else:
            print('mac address should be in format: xx:xx:xx:xx:xx')

    return mac

def validate_ip(ip):

    valid_ip = ''
    try:
        valid_ip = ipaddress.ip_address(ip)   
    except ValueError:
        print('ip address \'{}\' is not valid: '.format(ip))
  
    return valid_ip

def validate_mac(mac):
    mac_regex = '[0-9a-f]{2}(:)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$'
    
    return True if re.match(mac_regex, mac.lower()) else False


def validate_port(port):
    invalid_ports = [80, 443, 6443, 22623]
    while True:
        try:
            integer_check = port.isdigit()
            if integer_check:
                invalid_ports.index(int(port))
            else:
                print('port has to be an integer')
            print('ports {} are not allowed'.format(invalid_ports))
            port = input('enter a port: ')
        except AttributeError:
            print('ports {} are not allowed'.format(invalid_ports))
            port = input('enter a port: ')
        except ValueError:
            break

    return port

def validate_network_cidr(network_cidr):
    while True:
        try:
            ipaddress.ip_network(network_cidr)
        except ValueError:
            print('input should be in format x.x.x.x/x')
            network_cidr = input('enter the network cidr: ')

    return network_cidr
    

def validate_cidr(cidr):
    while True:
        integer_check = cidr.isdigit()
        if integer_check and int(cidr) < 32:
            break
        else:
            print('cidr has to be an integer and less than 32')
            cidr = input('enter the cidr notation for ips in each host: ')

    return cidr
            

def connect_to_idrac(user, passwd, base_api_url):
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    
    response = ''
    try:
        response = requests.get(base_api_url, verify=False, auth=(user, passwd))
    except requests.exceptions.ConnectTimeout:
        print('failed to establish connection to base api url')
    except Exception as e:
        print('unknown exception occurred') 
        print('{}'.format(e))  
    
    return response

def get_network_devices(user, passwd, base_api_url):
    network_devices = ''
    response = connect_to_idrac(user, passwd, base_api_url)
    if response and response.json():
        network_devices_info = response.json()
        try:
            network_devices = network_devices_info[u'Members']
        except KeyError:
            network_devices = ''

    return network_devices
        

def generate_network_devices_menu(devices):
    menu = {}
    i = 1
    choice = ''
    devices.sort()
    for device in devices:
        menu[i] = device
        i += 1
    while True:
        options = menu.keys()
        for entry in options:
            print('{} -> {}'.format(entry, menu[entry]))
        choice = input('Select the interface used by DHCP: ')
        if choice == '1' or choice == '2' or choice == '3' or choice == '4':
            break
        else:
            print('unknown option selected')

    selected_network_device = menu[int(choice)]
    print('selected interface is: {}'.format(menu[int(choice)]))
    
    return selected_network_device
        
def get_mac_address(selected_network_device, base_api_url, user, passwd):

    url = '{}/{}'.format(base_api_url, selected_network_device)
    print(url)
    device_mac_address = ''
    try:
        response = requests.get(url,verify=False,auth=(user, passwd))
    except requests.exceptions.ConnectionTimeout:
        print('failed to establish connection to get mac address')

    try:
        network_device_info = response.json()
    except ValueError:
        print('check URL, iDRAC user and password may be invalid')
        print('{}'.format(url))

    try:
        device_mac_address = network_device_info[u'MACAddress']
    except KeyError:
        print('No MAC Address found for network devices')
        print('{}'.format(selected_network_device))

    return device_mac_address

def get_network_device_mac(node_type='', ip_type=''):
    devices = []
    network_device_mac_address = ''
    #base_api_url = 'https://100.82.34.20/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces'
    
    ip = get_ip(node_type=node_type, ip_type=ip_type)
    user = input('enter the idrac user for {}: '.format(node_type))
    passwd = input('enter the idrac password for {}: '.format(node_type))
    base_api_url = 'https://{}/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces'.format(ip)
    #network_devices = get_network_devices(user, passwd, base_api_url)
    #network_devices = get_network_devices('root', 'Dell0SS!', base_api_url)
    network_devices = get_network_devices(user, passwd, base_api_url)
    if network_devices:
        for network_device in network_devices:
            device = list(map(lambda interface: interface.encode('ascii'), network_device.values()))
            try:
                devices.append(device[0].decode("utf-8").split('/')[-1])
            except IndexError:
                print('Did not find any network devices')

    if devices:
        print(devices)
        selected_network_device = generate_network_devices_menu(devices)
        print(selected_network_device)
        print(type(selected_network_device))
        network_device_mac_address = get_mac_address(selected_network_device, base_api_url, user, passwd)

    if network_device_mac_address:
        print(network_device_mac_address)
        print(type(network_device_mac_address))
        print('device {} mac address is {}'.format(selected_network_device, network_device_mac_address))
 
    return network_device_mac_address
    
def main():
    #get_network_device_mac(node_type='bootstrap')
    pass

if __name__ == "__main__":
    main()
