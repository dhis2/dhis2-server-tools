#!/usr/bin/env bash
set -e 
sudo ansible-playbook dhis2.yml --tags postgresql-install

