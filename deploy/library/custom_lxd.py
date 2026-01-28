#!/usr/bin/env python3

# (c) 2013, Michael Scherer <misc@zarb.org>
# (c) 2014, Hiroaki Nakamura <hnakamur@gmail.com>
# (c) 2016, Andew Clarke <andrew@oscailte.org>
#
# This file is based on https://github.com/ansible/ansible/blob/devel/plugins/inventory/libvirt_lxc.py which is part of Ansible,
# and https://github.com/hnakamur/lxc-ansible-playbooks/blob/master/provisioning/inventory-lxc.py
#
# NOTE, this file has some obvious limitations, improvements welcome
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
from subprocess import Popen, PIPE
import shutil
import sys
import json

# Path to static inventory file (relative to this script's location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_INVENTORY = os.path.join(SCRIPT_DIR, '..', 'inventory', 'hosts')

# Set up defaults
connection = 'lxd'


def parse_static_inventory(inventory_path):
    """
    Parse Ansible INI inventory file and return:
    - groups: dict of group_name -> list of hostnames
    - group_vars: dict of group_name -> dict of variables
    - host_vars: dict of hostname -> dict of variables
    """
    groups = {}
    group_vars = {}
    host_vars = {}
    current_section = None
    is_vars_section = False

    if not os.path.exists(inventory_path):
        return groups, group_vars, host_vars

    with open(inventory_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Check for section header [group] or [group:vars]
            section_match = re.match(r'^\[([^\]]+)\]$', line)
            if section_match:
                section_name = section_match.group(1)
                if ':vars' in section_name:
                    # This is a vars section like [all:vars] or [instances:vars]
                    current_section = section_name.replace(':vars', '')
                    is_vars_section = True
                    if current_section not in group_vars:
                        group_vars[current_section] = {}
                else:
                    # This is a host group section
                    current_section = section_name
                    is_vars_section = False
                    if current_section not in groups:
                        groups[current_section] = []
                continue

            if is_vars_section and current_section:
                # Parse variable assignment (key=value)
                if '=' in line:
                    key, value = line.split('=', 1)
                    group_vars[current_section][key.strip()] = value.strip()
            elif current_section:
                # Parse host entry with optional inline variables
                # Format: hostname  var1=val1  var2=val2
                parts = line.split()
                if parts:
                    hostname = parts[0]
                    groups[current_section].append(hostname)

                    # Parse inline host variables
                    if len(parts) > 1:
                        if hostname not in host_vars:
                            host_vars[hostname] = {}
                        for part in parts[1:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                host_vars[hostname][key.strip()] = value.strip()
            else:
                # Hosts before any section (ungrouped)
                parts = line.split()
                if parts:
                    hostname = parts[0]
                    if 'ungrouped' not in groups:
                        groups['ungrouped'] = []
                    groups['ungrouped'].append(hostname)

                    if len(parts) > 1:
                        if hostname not in host_vars:
                            host_vars[hostname] = {}
                        for part in parts[1:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                host_vars[hostname][key.strip()] = value.strip()

    return groups, group_vars, host_vars


def get_lxd_containers():
    """
    Query LXD for running containers and return dict of name -> ip
    Also return dict of name -> group (from user.type config)
    """
    containers = {}
    container_groups = {}

    if not shutil.which('lxc'):
        return containers, container_groups

    pipe = Popen(['lxc', 'list', '--format', 'json'], stdout=PIPE, universal_newlines=True)
    lxdjson = json.load(pipe.stdout)

    for item in lxdjson:
        if 'state' in item and item['state'] is not None and 'network' in item['state']:
            network = item['state']['network']
            name = item['name']
            group = item['config'].get('user.type', None)

            if 'eth0' in network and 'addresses' in network['eth0']:
                for address in network['eth0']['addresses']:
                    if address.get('family') == 'inet' and 'address' in address:
                        containers[name] = address['address']
                        if group:
                            container_groups[name] = group
                        break

    return containers, container_groups


def build_inventory():
    """
    Build merged inventory from static file and dynamic LXD discovery.
    - Static inventory provides: groups, group_vars, host_vars
    - LXD provides: dynamic IPs (override static ansible_host)
    """
    result = {'_meta': {'hostvars': {}}}

    # Parse static inventory
    groups, group_vars, host_vars = parse_static_inventory(STATIC_INVENTORY)

    # Get dynamic LXD containers
    lxd_containers, lxd_groups = get_lxd_containers()

    # Get connection type from static inventory
    global connection
    if 'all' in group_vars and 'ansible_connection' in group_vars['all']:
        connection = group_vars['all']['ansible_connection']

    # Build groups from static inventory
    for group_name, hosts in groups.items():
        if group_name not in result:
            result[group_name] = {'hosts': []}
        for hostname in hosts:
            if hostname not in result[group_name]['hosts']:
                result[group_name]['hosts'].append(hostname)

    # Add LXD containers to their groups (based on user.type)
    for container_name, group in lxd_groups.items():
        if group not in result:
            result[group] = {'hosts': []}
        if container_name not in result[group]['hosts']:
            result[group]['hosts'].append(container_name)

    # Add LXD containers without user.type to ungrouped (if not already in a group)
    all_grouped_hosts = set()
    for group_name, group_data in result.items():
        if group_name != '_meta' and 'hosts' in group_data:
            all_grouped_hosts.update(group_data['hosts'])

    for container_name in lxd_containers:
        if container_name not in all_grouped_hosts:
            if 'ungrouped' not in result:
                result['ungrouped'] = {'hosts': []}
            if container_name not in result['ungrouped']['hosts']:
                result['ungrouped']['hosts'].append(container_name)

    # Build host variables
    all_hosts = set()
    for group_name, hosts in groups.items():
        all_hosts.update(hosts)
    all_hosts.update(lxd_containers.keys())

    for hostname in all_hosts:
        hostvars = {}

        # Apply group variables (all:vars first, then specific groups)
        if 'all' in group_vars:
            hostvars.update(group_vars['all'])

        # Apply group-specific vars for groups this host belongs to
        for group_name, hosts in groups.items():
            if hostname in hosts and group_name in group_vars:
                hostvars.update(group_vars[group_name])

        # Apply host-specific variables from static inventory
        if hostname in host_vars:
            hostvars.update(host_vars[hostname])

        # Override ansible_host with dynamic LXD IP if available
        if hostname in lxd_containers:
            hostvars['ansible_host'] = lxd_containers[hostname]
            if 'ansible_connection' not in hostvars:
                hostvars['ansible_connection'] = connection

        # Special case for localhost/127.0.0.1
        if hostname in ('localhost', '127.0.0.1'):
            hostvars['ansible_connection'] = 'local'
            hostvars['ansible_host'] = '127.0.0.1'

        result['_meta']['hostvars'][hostname] = hostvars

    return result


def get_host_vars(hostname):
    """Get variables for a specific host."""
    inventory = build_inventory()
    return inventory['_meta']['hostvars'].get(hostname, {})


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        print(json.dumps(build_inventory()))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print(json.dumps(get_host_vars(sys.argv[2])))
    else:
        print("Usage: {} --list | --host <hostname>".format(sys.argv[0]))
