#!/usr/bin/env bash
set -e 
sudo ansible-playbook dhis2.yml -t create-instance 
