## bash
# install lxd on the host
sudo snap install lxd
# install ansible 
#sudo apt install ansible # this will not include cummunity modules like ufw, its recommended installing ansible with pip
# install pip3 
sudo apt -y install python3-pip
sudo apt-get install -y python-netaddr #required for ipaddr filter

# install ansible
# Since pip does not coordinate with system package managers, it could make changes to your system that leaves it in an inconsistent or non-functioning state, its recommended using pip3 with --user
sudo pip3 install ansible


# Ensure a user is a member of lxd group
# sudo usermod -aG lxd $USER


