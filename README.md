# Master branch is updated with OCP45 CSI contents

```
$ python3 generate_inventory_file.py -h
usage: generate_inventory_file.py [-h] [--run | --add] [--id_user ID_USER]
                                  [--id_pass ID_PASS] [--debug]

Generate Inventory

optional arguments:
  -h, --help         show this help message and exit
  --run              generate inventory file
  --add              number of worker nodes
  --id_user ID_USER  specify idrac user
  --id_pass ID_PASS  specify idrac user
  --debug            specify debug logs
```

- run option will generate inventory file
- add option will add new worker nodes to an already existing inventory file.
- specify common idrac user and password using --id_user and --id_pass arguments 
- debug enables logging.debug level for the execution


For OCP 43 CSI contents - Refer to https://github.com/dell-esg/openshift-bare-metal

Switch Config
> - Switches S3048, S5232F config files are saved in examples directory
> - S5232F x 2 configured in VLTi
> - S3048 used for iDRAC purposes

Python Script - Pre-Reqs
> - RHEL OS (Tested in 7.8)
> - Python3
> - pip3 packages (pyyaml, requests)

Python Script - Output
> - An inventory file used by ansible to execute roles defined in ocp.yml
> - Script log file (*Inventory.log by default*)

Ansible Playbooks - Pre-Reqs
> - RedHat subscription (to download ansible rpm and pullsecret for OCP 4.3)
> - Inventory File (generated using python script)

Ansible Playbooks - Execution
> - cd *git clone dir/containers/ansible*
> - *ansible-playbook -i 'Path to inventory file path generated using python script' ocp.yml*

Ansible Playbooks - Output
> - Services such as *DNS/DHCP/PXE/TFTP/HAProxy* are configured in local node using the inventory file generated. 

Note: Dell CSI drivers for OCP 4.3 currently supports only RHEL worker nodes. 
