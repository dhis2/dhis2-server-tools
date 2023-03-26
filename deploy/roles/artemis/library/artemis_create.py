#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os

"""
Ansible module to create artemis broker
(c) 2017, Matthieu Rémy <remy.matthieu@gmail.com>
"""

DOCUMENTATION = '''
---
module: artemis_create
short_description: Creates an artemis broker.
description:
    - Creates an artemis broker.
options:
    name:
        description:
            - broker name
        required: true
        default: null
    path:
        description:
            - broker path
        required: true
        default: null
    user:
        description:
            - user name to connect to thebroker
        required: true
        default: null
    password:
        description:
            - user password to connect to the broker
        required: true
        default: null
'''

EXAMPLES = '''
# Create artemis broker named 'artemis-broker' with a user / password : admin / admin
- artemis_create: state="present" name="artemis-broker" user="admin" password="admin"
'''

CREATE_BROKER_COMMAND = "{0}/bin/artemis create {1}/{2} --user {3} --password {4} --allow-anonymous"


def create_broker(artemis_home, ansible_module, name, path, user, password):
    """Call artemis bin command to create a broker

    :param artemis_home: artemis home
    :param ansible_module: ansible module
    :param name: broker name
    :param name: broker path
    :param user: broker user
    :param password: broker password
    :return: command, ouput command message, error command message
    """

    changed = False
    cmd = CREATE_BROKER_COMMAND.format(artemis_home, path, name, user, password)
    out = ""
    err = ""

    if not os.path.isdir(name):
        rc, out, err = ansible_module.run_command(cmd)
        changed = True

        if len(err) > 0:
            ansible_module.fail_json(msg=err)

    return changed, cmd, out, err


def main():
    fields = {
        "name": {"required": True, "type": "str"},
        "path": {"required": True, "type": "str"},
        "user": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str", "no_log": True},
        "artemis_home": {"default": "/opt/artemis", "type": "str"}
    }

    ansible_module = AnsibleModule(argument_spec=fields)

    name = ansible_module.params["name"]
    path = ansible_module.params["path"]
    artemis_home = ansible_module.params["artemis_home"]
    user = ansible_module.params["user"]
    password = ansible_module.params["password"]

    changed, cmd, out, err = create_broker(artemis_home, ansible_module, name, path, user, password)

    ansible_module.exit_json(changed=changed, cmd=cmd, name=name, stdout=out, stderr=err)

if __name__ == '__main__':
    main()
