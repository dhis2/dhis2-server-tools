#!/usr/bin/env bash
set -e 

# Check the version of Ubuntu running
distro_name=$(lsb_release -i | cut -f2)
distro_version=$(lsb_release -r | cut -f2)

# UFW status 
UFW_STATUS=$(sudo ufw status |grep Status|cut -d ' ' -f 2)

# ensure firewall is running on the host
if [[ $UFW_STATUS == "inactive" ]]; then
    echo ""
    echo "============================= ERROR ================================="
    echo "ufw firewall needs to be enabled in order to perform the installation."
    echo "Use Bellow commands to allow your ssh port (default=22) and enable the firewall"
    echo "sudo ufw limit 22/tcp"
    echo "sudo ufw enable"
    echo "sudo ./deploy.sh"
    echo ""
    exit 1
fi

# Ensure inventory file is created before doing anything
hosts_file="inventory/hosts"
if [ ! -f "$hosts_file" ]; then
    echo "$hosts_file file does not exist, creating one from hosts.template"
    cp inventory/hosts.template inventory/hosts
    echo ""
    echo ""
    sleep 2
fi

# install ansible on Ubuntu 20.04 
ansible_install_2004() {
  sudo apt -yq update
  sudo apt install -yq  git
  sudo apt install -yq software-properties-common   
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -yq  ansible
  }
# install ansible on Ubuntu-22.04
  ansible_install_2204() {
  # disables needrestart dialog on ubuntu 22.04 
  if [ -f "/etc/needrestart/needrestart.conf" ]; then
  sed -i 's/#$nrconf{restart} = '"'"'i'"'"';/$nrconf{restart} = '"'"'a'"'"';/g' /etc/needrestart/needrestart.conf 
  sed -i "s/#\$nrconf{kernelhints} = -1;/\$nrconf{kernelhints} = -1;/g" /etc/needrestart/needrestart.conf  
  fi
  sudo apt -yq update
  sudo apt install -yq  git
  sudo apt install -yq software-properties-common
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -yq ansible
}

# this is for other releases, -- but they have to be newer that ubuntu 20.04
ansible_install_other() {
  sudo apt -yq update
  sudo apt install -yq  git
  sudo apt install -yq software-properties-common
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
         if (( $(echo "${distro_version} > 22.04" | bc -l) )); then
            echo "Installing ansible on ${distro_name} ${distro_version} ..."
           echo "Please note that your distro is not either Ubuntu 20.04 or 22.04, the setup in your system is experimental i.e not tested extensively"
           ansible_install_other
        else
          echo "Your distro  ${distro_name} ${distro_version}  is not supported"
          exit 1
        fi 
        ;;
      esac
    sudo -E apt-get -yq autoclean
    # install community general collections 
    ansible-galaxy collection install community.general
fi

# deploying dhis2 
if [ $(cat inventory/hosts  | grep -Po '(?<=ansible_connection=)([a-z].*)') == "lxd" ]
  then
     # deploying dhis2 in lxd containers
     echo "Deploying dhis2 with lxd ..."
     # Ensure you community general callections are upgraded, 
     ansible-galaxy collection install community.general --upgrade
     sudo ansible-playbook dhis2.yml
  else
     # deploying dhis2 over ssh
     echo "Deploy dhis2 over ssh ..."
     read -p "Enter ssh user: " ssh_user
     # Check if group exists and add user silently
      if ! getent group 'lxd' >/dev/null 2>&1; then
        usermod -a -G "lxd" "$ssh_user"
      fi
     # usermod -a -G lxd $ssh_user
     su -c "ansible-playbook  dhis2.yml -kK" $ssh_user
fi
