#!/usr/bin/env bash
# update the system 
sudo apt update     
# install ansible
sudo apt install software-properties-common                 # adds sofware properties common 
sudo apt-add-repository --yes --update ppa:ansible/ansible  # adds ansible repository
sudo apt install ansible                                    # installs ansible
# install python3-netaddr required for ansible.utils.ipaddr utility
sudo apt-get install -y python3-netaddr   
# install community general collections 
ansible-galaxy collection install community.general -f

# ansible-galaxy collection install -r requirements.yml

