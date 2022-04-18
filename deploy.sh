## bash
# install lxd on the host with snap
sudo snap install lxd

# sudo ansible-galaxy collection install community.general
# this will not include cummunity modules like ufw, its recommended installing ansible with pip
# install pip3 
sudo apt-get install -y python-netaddr #required for ipaddr filter
# ------------------------------
# install ansible with pip
# ------------------------------
# Since pip does not coordinate with system package managers, it could make changes to your system that leaves it in an inconsistent or non-functioning state, its recommended using pip3 with --user
sudo apt install python3-pip                                # installs  pip3 on Debian like systems.
sudo pip3 install ansible                                   # installs ansible with pip3

# ------------------------
# install ansible with apt
# ------------------------
sudo apt update                                             # updates system packages 
sudo apt install software-properties-common                 # adds sofware properties common 
sudo apt-add-repository --yes --update ppa:ansible/ansible  # adds ansible repository
sudo apt install ansible                                    # installs ansible

# -----------------------------------------------
# install community general collections manually
# -----------------------------------------------
ansible-galaxy collection install community.general -f      # add community general collections, required if ansible is installed with apt. 

# Ensure a user is a member of lxd group
# sudo usermod -aG lxd $USER


