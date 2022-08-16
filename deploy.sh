#!/usr/bin/env bash
# install ansible with apt
sudo apt update                                             # updates system packages 
sudo apt install software-properties-common                 # adds sofware properties common 
sudo apt-add-repository --yes --update ppa:ansible/ansible  # adds ansible repository
sudo apt install ansible                                    # installs ansible
# ansible dependency 
sudo apt-get install -y python3-netaddr                      # used for chencking whether a given address is withing a given network

# install community general collections 
ansible-galaxy collection install community.general -f      # add community general collections, required if ansible is installed with apt. 

