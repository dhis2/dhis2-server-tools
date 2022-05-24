# dhis2-server-tools
Tools to support installation and management of DHIS2 using ansible.
## Introduction

## Requirements/ Pre-requisites 

* an ubuntu 20.04 server(s)
* non root user with sudo privileges
## Dependencies/Required system packages
* lxd container engine (required if dhis2 is setup on single host)
* ansible 
* backend servers (required if dhis2 is setup in a distributed environment)

## Pre-requisites 
* an ubuntu 20.04 server/servers  
* non root user with sudo privileges
* ssh access to the server(s)

## Steps to deploy dhis2
* Pull the code from git
* navigate to the directory pulled from git 
* run deploy shell scrip with sudo ./deploy.sh 
  * update and upgrade the server 
  * install
    * lxd
    * ansible
    * ansible community general modules
    * python-netaddr 
* cd to deploy directoy 
* setup lxd enviroment with ansible-playbook lxd_init.sh
* spin up dhis2 with ansible-playbook dhis2

## NOTE
This tools are work in progress and not production ready.<br/>
Please refer to https://github.com/bobjolliffe/dhis2-tools-ng for production ready dhis2 installation guide. 
