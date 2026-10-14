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
    # Pre-seed grub-pc's boot-device debconf answer before any apt operation
    # that might install/reconfigure it. On QEMU/KVM VMs this question can be
    # genuinely unanswered until a kernel-related update pulls grub-pc in as
    # a dependency - DEBIAN_FRONTEND=noninteractive alone doesn't help then,
    # since with no existing answer to fall back to, grub-install fails
    # outright ("/multiselect does not exist") instead of just proceeding.
    # Harmless to seed even if grub-pc never ends up installed (e.g. UEFI
    # boots use grub-efi instead and never ask this).
    root_src="$(findmnt -no SOURCE / 2>/dev/null)"
    boot_disk="$(lsblk -ndo pkname "$root_src" 2>/dev/null | head -n1)"
    # lsblk pkname only resolves a partition to its parent disk - if root is
    # mounted directly on a whole disk (no partition table), it returns
    # nothing, and the disk's own name (e.g. sda) is already what's needed.
    [[ -z "$boot_disk" ]] && boot_disk="$(basename "${root_src:-}" 2>/dev/null)"
    if [[ -n "$boot_disk" ]]; then
        echo "grub-pc grub-pc/install_devices multiselect /dev/${boot_disk}" | sudo debconf-set-selections
        echo "grub-pc grub-pc/install_devices_empty boolean false" | sudo debconf-set-selections
    fi
    sudo apt -yq update
    sudo DEBIAN_FRONTEND=noninteractive apt install -yq git software-properties-common sshpass
    sudo apt-add-repository --yes --update ppa:ansible/ansible
    sudo DEBIAN_FRONTEND=noninteractive apt install -yq ansible
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

# Ensure required collections are installed. community.mysql is needed only
# when Doris is being provisioned - the doris role's own preflight check
# (roles/doris/tasks/main.yml) fails fast with install instructions in that
# case, instead of installing it unconditionally here on every deploy
# regardless of whether Doris is even configured.
#
# No --upgrade here deliberately: plain "install" short-circuits instantly
# once satisfied (see the identical check a few lines up, gated on ansible
# not yet being installed), but --upgrade forces ansible-galaxy through its
# full dependency-resolution map against the Galaxy API on every single
# deploy run, every time - genuinely slow for a collection the size of
# community.general, not stuck/network-broken, just an expensive check paid
# on every run for something that changes rarely. Run
# `ansible-galaxy collection install community.general --upgrade` by hand
# when you actually want to pick up a newer release.
ansible-galaxy collection install community.general

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
