import argparse
import json
import re
import requests
import sys

from urllib3.exceptions import InsecureRequestWarning


def get_network_devices_info(idrac_user, idrac_pass, base_api_url):
    
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    try:
        response = requests.get(base_api_url, verify=False, auth=(idrac_user,idrac_pass))
    except requests.exceptions.ConnectTimeout:
        print('failed to establish connection to base api url')
        sys.exit()

    try:
        network_devices_info = response.json()
    except AttributeError:
        print('response has no JSON payload')
    except ValueError:
        print('Check base API URL, iDRAC user and password may be invalid')
        sys.exit()

    try:
        network_devices = network_devices_info[u'Members']
    except KeyError:
        print('no network devices found')
        sys.exit()

    devices = []

    for network_device in network_devices:
        device = list(map(lambda interface: interface.encode('ascii'), network_device.values()))

        try:
            devices.append(device[0].decode("utf-8").split('/')[-1])
        except IndexError:
            print('Did not find any network devices')
            sys.exit()

    return devices


def get_mac_address(network_devices, idrac_user, idrac_pass, base_api_url):
    network_devices_mac_address = {}
    for each_network_device in network_devices:
        url = '{}/{}'.format(base_api_url, each_network_device)

        try:
            response = requests.get(url,verify=False,auth=(idrac_user,idrac_pass))
        except requests.exceptions.ConnectTimeout:
            print('failed to establish connection to base api url')
            sys.exit()

        try:
            network_device_properties = response.json()
        except ValueError:
            print('Check base API URL, iDRAC user and password may be invalid')
            sys.exit()

        try:
            device_mac_address = network_device_properties[u'MACAddress']
            network_devices_mac_address[each_network_device] = device_mac_address
        except KeyError:
            print('No MAC Address found for network device: {}'.format(each_network_device))
            device_mac_address = 'MAC Address Not Found'

    if network_devices_mac_address:
        print('************NETWORK_DEVICES_MAC_ADDRESSES**********')
        for each_device_mac_address in network_devices_mac_address.items():
            print(each_device_mac_address)
        print('***************************************************')
    else:
        print('Could not find Mac addresses')

    #return network_device_mac_address



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--idrac_ip', help='provide idrac_ip', required=True)
    parser.add_argument('--idrac_user', help='provide idrac user', required=True)
    parser.add_argument('--idrac_pass', help='provide idrac password', required=True)
    args = parser.parse_args()

    idrac_ip = args.idrac_ip
    idrac_user = args.idrac_user
    idrac_pass = args.idrac_pass
    base_api_url = 'https://{}/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces'.format(idrac_ip)

    network_devices = get_network_devices_info(idrac_user, idrac_pass, base_api_url)
    
    #mac_address = get_mac_address(network_devices, idrac_user, idrac_pass, base_api_url)
    get_mac_address(network_devices, idrac_user, idrac_pass, base_api_url)
    #print('********************iDRAC IP - {} *****************'.format(idrac_ip))
    #print('************NETWORK_DEVICES_MAC_ADDRESSES**********')
    #print('{}'.format(mac_address))
    #print('***************************************************')
   

if __name__ == "__main__":
    main()
