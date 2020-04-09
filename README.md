# Master branch is updated with OCP43 contents
# For OCP42 contents, switch to branch ocp42.

Switch Config
> - Switches S3048, S5232F config files are saved in examples directory
> - S5232F x 2 configured in VLTi
> - S3048 used for iDRAC purposes

Python Script - Pre-Reqs
> - RHEL OS (Tested in 7.6)
> - Python3
> - pip3 packages (pyyaml, requests)

Python Script - Execution
> - python3 generate_inventory_file.py
> Refer to Page 15 Chapter 3 in [OCP 4.3 Deployment Guide](https://www.dellemc.com/resources/en-us/asset/technical-guides-support-information/solutions/h18212-openshift-container-dpg.pdf)

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
