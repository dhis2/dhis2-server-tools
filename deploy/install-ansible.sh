#!/usr/bin/env bash
set -e 

# Check the version of Ubuntu running
distro_name=$(lsb_release -i | cut -f2)
distro_version=$(lsb_release -r | cut -f2)
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

