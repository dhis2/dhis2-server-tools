#!/usr/bin/env bash
set -eo pipefail

# Show help
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "Usage: sudo ./deploy.sh"
    echo ""
    echo "Deploys DHIS2 using Ansible, either in LXD containers or over SSH."
    echo "Requires ufw firewall to be enabled before running."
    exit 0
fi

# Check the version of Ubuntu running using /etc/os-release
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    distro_name=$ID
    distro_version=$VERSION_ID
else
    distro_name=$(lsb_release -i | cut -f2)
    distro_version=$(lsb_release -r | cut -f2)
fi

# UFW status
UFW_STATUS=$(ufw status | grep Status | cut -d ' ' -f 2)

# ensure firewall is running on the host
if [[ "$UFW_STATUS" == "inactive" ]]; then
    echo "" >&2
    echo "============================= ERROR =================================" >&2
    echo "ufw firewall needs to be enabled in order to perform the installation." >&2
    echo "Use the commands below to allow your ssh port (default=22) and enable the firewall" >&2
    echo "sudo ufw limit 22/tcp" >&2
    echo "sudo ufw enable" >&2
    echo "sudo ./deploy.sh" >&2
    echo "" >&2
    exit 1
fi

# Ensure inventory file is created before doing anything
hosts_file="inventory/hosts"
if [[ ! -f "$hosts_file" ]]; then
    echo "$hosts_file file does not exist, creating one from hosts.template"
    cp inventory/hosts.template inventory/hosts
    chown "${SUDO_USER:-$USER}" inventory/hosts
    chmod 600 inventory/hosts
    echo ""
elif [[ "$(stat -c '%a' "$hosts_file")" != "600" ]]; then
    echo "Fixing permissions on $hosts_file"
    chown "${SUDO_USER:-$USER}" inventory/hosts
    chmod 600 inventory/hosts
fi

# Install ansible on Ubuntu
ansible_install() {
    # Disable needrestart dialog on Ubuntu 22.04+
    if [[ -f "/etc/needrestart/needrestart.conf" ]]; then
        sed -i 's/#$nrconf{restart} = '"'"'i'"'"';/$nrconf{restart} = '"'"'a'"'"';/g' /etc/needrestart/needrestart.conf
        sed -i "s/#\$nrconf{kernelhints} = -1;/\$nrconf{kernelhints} = -1;/g" /etc/needrestart/needrestart.conf
    fi
    sudo apt -yq update
    sudo apt install -yq git software-properties-common sshpass
    sudo apt-add-repository --yes --update ppa:ansible/ansible
    sudo apt install -yq ansible
    return 0
}

if ! command -v ansible &> /dev/null; then
    # Check minimum version requirement (20.04)
    # Compare versions by removing dots and comparing as integers (e.g., 20.04 -> 2004)
    min_version="2004"
    current_version="${distro_version//./}"
    if [[ "$current_version" -lt "$min_version" ]]; then
        echo "Your distro ${distro_name} ${distro_version} is not supported (minimum: 20.04)" >&2
        exit 1
    fi
    echo "Installing ansible on ${distro_name} ${distro_version} ..."
    ansible_install
    sudo -E apt-get -yq autoclean
    # Install community general collections
    ansible-galaxy collection install community.general
fi

# Ensure community general collections are upgraded
ansible-galaxy collection install community.general --upgrade

# Check if any host explicitly uses ssh connection (per-host or per-group override)
# Hosts may use lxd (default) or ssh individually — Ansible handles per-host connection natively.
has_ssh_hosts=$(grep -v '^\s*#' inventory/hosts | sed 's/#.*//' | grep -E 'ansible_connection=ssh' || true)

if [[ -n "$has_ssh_hosts" ]]; then
    # At least one host uses SSH — need credentials for those hosts
    echo ""
    echo "Deploying dhis2 (hybrid lxd/ssh connections detected) ..."
    ssh_user="${SUDO_USER:-$USER}"
    if getent group 'lxd' >/dev/null 2>&1; then
        sudo usermod -a -G "lxd" "$ssh_user"
    fi
    su -c "ansible-playbook dhis2.yml -kK" "$ssh_user"
else
    # All hosts use lxd (default)
    echo "Deploying dhis2 with lxd ..."
    sudo ansible-playbook dhis2.yml
fi
