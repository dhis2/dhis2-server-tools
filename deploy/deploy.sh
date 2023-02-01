#!/usr/bin/env bash
# installing ansible 
set -e 
if ! command -v ansible &> /dev/null
then
  export DEBIAN_FRONTEND=noninteractive
  RED='\033[0;31m'
  sudo -E apt -yq update
  sudo -E apt -yq  upgrade

  # install git if not present 
  sudo apt install -yqq  git 
# install ansible
  sudo apt install -yqq software-properties-common   
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -yqq  ansible
# install python3-netaddr required for ansible.utils.ipaddr utility
  sudo -E apt-get install -yqq python3-netaddr
  sudo -E apt-get -qy autoclean

# install community general collections 
  ansible-galaxy collection install community.general
fi

if [ $(cat inventory/hosts  | grep -Po '(?<=ansible_connection=)([a-z].*)') == "lxd" ]
then
   # ensure firewall is running on the host
   UFW_STATUS=$(sudo ufw status |grep Status|cut -d ' ' -f 2)
   if [[ $UFW_STATUS == "inactive" ]]; then
      echo
	    echo -e "\e ${RED}=========== ERROR =================="
	    echo "ufw firewall needs to be enabled in order to perform the installation."
	    echo "It is required to NAT connections to the proxy container."
	    echo "You just need to have a rule to allow ssh access. eg:"
	    echo "   sudo ufw limit 22/tcp"
	    echo "then, 'sudo ufw enable'"
	    echo "Then you can try to run sudo ./deploy.sh  again"
	    exit 1
  fi
   # deploying dhis2 in lxd containers
   echo "Deploying dhis2 with lxd ..."
   sudo ansible-playbook lxd_setup.yml
   sudo ansible-playbook dhis2.yml
else
   # deploying dhis2 over ssh
   echo "Deploy dhis2 over ssh ..."
   read -p "Enter ssh user: " ssh_user
   su -c "ansible-playbook  dhis2.yml -kK" $ssh_user
fi
