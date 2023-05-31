#!/usr/bin/env bash
set -e 
RED='\033[0;31m'

# Check the version of ubuntu running
distro_name=$(lsb_release -i | cut -f2)
distro_version=$(lsb_release -r | cut -f2)

# UFW status 
UFW_STATUS=$(sudo ufw status |grep Status|cut -d ' ' -f 2)

# ensure firewall is running on the host
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
# install ansible on ubuntu 20.04 
ansible_install_2004() {
  sudo apt -yq update
  # sudo apt -yq  upgrade
  sudo apt install -yq  git
  sudo apt install -yq software-properties-common   
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -yq  ansible
  }
# install ansible on ubutnu22.04
  ansible_install_2204() {
  sed -i 's/#$nrconf{restart} = '"'"'i'"'"';/$nrconf{restart} = '"'"'a'"'"';/g' /etc/needrestart/needrestart.conf  
  sed -i "s/#\$nrconf{kernelhints} = -1;/\$nrconf{kernelhints} = -1;/g" /etc/needrestart/needrestart.conf  
  sudo apt -yq update
  # sudo apt -yq  upgrade
  sudo apt install -yq  git
  sudo apt install -yq software-properties-common
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -yq ansible
}

if ! command -v ansible &> /dev/null
then
    case ${distro_version} in
      "20.04")
        echo "Installing ansible on ${distro_name} ${distro_version} LTS ..."
        ansible_install_2004
        ;;
      "22.04")
        echo "Installing ansible on ${distro_name} ${distro_version} LTS ..."
         ansible_install_2204
        ;;
      *)
        echo "Could not install DHIS2 on your Ubuntu version: $distro_version, please upgrade to 20.04|22.04"
        exit 1
        ;;
      esac
    sudo -E apt-get -yq autoclean
    # install community general collections 
    ansible-galaxy collection install community.general
fi

if [ $(cat inventory/hosts  | grep -Po '(?<=ansible_connection=)([a-z].*)') == "lxd" ]
then
    # deploying dhis2 in lxd containers
   echo "Deploying dhis2 with lxd ..."
   sudo ansible-playbook dhis2.yml
else
   # deploying dhis2 over ssh
   echo "Deploy dhis2 over ssh ..."
   read -p "Enter ssh user: " ssh_user
   su -c "ansible-playbook  dhis2.yml -kK" $ssh_user
fi
