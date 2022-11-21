#!/usr/bin/env bash
# update the system 
sudo apt -y  update     
sudo apt -y  upgrade     

# install git if not present 
sudo apt install -y git 
# install ansible
sudo apt install -y software-properties-common   
sudo apt-add-repository --yes --update ppa:ansible/ansible
sudo apt install -y  ansible
# install python3-netaddr required for ansible.utils.ipaddr utility
sudo apt-get install -y python3-netaddr

# install community general collections 
ansible-galaxy collection install community.general


if [ $(cat inventory/hosts  | grep -Po '(?<=ansible_connection=)([a-z].*)') == "lxd" ]
then
   UFW_STATUS=$(sudo ufw status |grep Status|cut -d ' ' -f 2)
   if [[ $UFW_STATUS == "inactive" ]]; then
      echo
	    echo "======= ERROR =========================================="
	    echo "ufw firewall needs to be enabled in order to perform the installation."
	    echo "It is required to NAT connections to the proxy container."
	    echo "You just need to have a rule to allow ssh access. eg:"
	    echo "   sudo ufw limit 22/tcp"
	    echo "then, 'sudo  ufw enable'"
	    echo "Then you can try to run sudo ./deploy.sh  again"
	    exit 1
  fi
   sudo ansible-playbook lxd_setup.yml
   sudo ansible-playbook dhis2.yml
else
   ansible-playbook dhis2.yml -kK 
fi

