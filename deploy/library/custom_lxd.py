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
from subprocess import Popen, PIPE
import shutil
import sys
import json

from ansible.module_utils.six.moves import configparser

# Set up defaults
resource = 'local:'
connection = 'lxd'
hosts = {}
result = {}

# persing INI file 
        # Read the settings from the lxd.ini file
        # config = configparser.ConfigParser(allow_no_value=True)
        # config.read('../inventory/hosts')
        
        # if config.has_option('all:vars', 'ansible_connection'):
            # ansible_connection = config.get('all:vars', 'ansible_connection')
        # print(ansible_connection)
        # if config.has_option('lxd', 'group'):
        #     group = config.get('lxd', 'group')
        # if config.has_option('lxd', 'connection'):
        #     connection = config.get('lxd', 'connection')

if shutil.which('lxc'):
    # Set up containers result and hosts array
    # Run the command and load json result
    pipe = Popen(['lxc', 'list', '--format', 'json'], stdout=PIPE, universal_newlines=True)
    lxdjson = json.load(pipe.stdout)
    # Iterate the json lxd output
    for item in lxdjson:

        # Check state and network
        if 'state' in item and item['state'] is not None and 'network' in item['state']:
            network = item['state']['network']
            new_group = item['config'].get('user.type', 'ungrouped')
            # try:
            #     new_group = item['config']['user.type']
            # except KeyError:
            #     new_group = "ungrouped"

            # Check for eth0 and addresses
            if 'eth0' in network and 'addresses' in network['eth0']:
                addresses = network['eth0']['addresses']
                            
                # Iterate addresses
                for address in addresses:

                    # Only return inet family addresses
                    if 'family' in address and address['family'] == 'inet':
                        if 'address' in address:
                            ip = address['address']
                            name = item['name']
                            if new_group not in result:
                                    # if new_group not in results:
                                result[new_group] = {}
                                result[new_group]['hosts'] = []
                            result[new_group]['hosts'].append(name)
                            result[new_group]['vars'] = {}
                            result[new_group]['vars']['ansible_connection'] = connection
                            result[new_group]['vars']['ansible_host'] = ip

if len(sys.argv) == 2 and sys.argv[1] == '--list':
    print(json.dumps(result))
elif len(sys.argv) == 3 and sys.argv[1] == '--host':
    if sys.argv[2] == 'localhost':
        print(json.dumps({'ansible_connection': 'local'}))
    else:
        if connection == 'lxd':
            print(json.dumps({'ansible_connection': connection}))
        else:
            print(json.dumps({'ansible_connection': connection, 'ansible_host': hosts[sys.argv[2]]}))
else:
    print("Need an argument, either --list or --host <host>")
