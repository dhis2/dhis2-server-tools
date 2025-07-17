Table of contents
---
<!-- vim-markdown-toc GFM -->

* [Introduction](#introduction)
* [Installation with LXD containers](#installation-with-lxd-containers)
	* [Step 0 — Before you start](#step-0--before-you-start)
	* [Step 1 — SSH to your server (where you want to install DHIS2) and enable firewall.](#step-1--ssh-to-your-server-where-you-want-to-install-dhis2-and-enable-firewall)
	* [Step 2 — Grab the deployment tools from github](#step-2--grab-the-deployment-tools-from-github)
	* [Step 3 —  Create inventory hosts file](#step-3---create-inventory-hosts-file)
	* [Step 4 — Set fqdn, email, and timezone](#step-4--set-fqdn-email-and-timezone)
	* [Step 5 — The Install](#step-5--the-install)
* [Install on physical/virtual servers.](#install-on-physicalvirtual-servers)
	* [Step 0: Before you start, make sure you have the following:](#step-0-before-you-start-make-sure-you-have-the-following)
	* [Step 1: Access deployment server (ansible-controller) via SSH](#step-1-access-deployment-server-ansible-controller-via-ssh)
	* [Step 2: Install ansible on the deployment server](#step-2-install-ansible-on-the-deployment-server)
	* [Step 3: Grab deployment tools from github](#step-3-grab-deployment-tools-from-github)
	* [Step 4: Create hosts file (from the hosts template)](#step-4-create-hosts-file-from-the-hosts-template)
	* [Step 5: Set fqdn, email, timezone and `ansible_connection=ssh`](#step-5-set-fqdn-email-timezone-and-ansible_connectionssh)
	* [Step 6:  Ensure connection to the managed hosts works](#step-6--ensure-connection-to-the-managed-hosts-works)
	* [Step 7: Run the playbook](#step-7-run-the-playbook)
* [Adding a new instance](#adding-a-new-instance)
* [Using a Custom TLS Certificate](#using-a-custom-tls-certificate)
* [Conclusion](#conclusion)
* [Other important links](#other-important-links)

<!-- vim-markdown-toc -->
---

## Introduction 
This is a quick DHIS2 install guide using [ansible](https://www.ansible.com/). At the end, you will have
one or more dhis2 instances running, configured with postgreSQL database and
nginx or apache2 proxy. Out of the box, you'll benefit from comprehensive application and server resource monitoring with Glowroot APM (Application Performance Monitoring) and a Munin instance. 

At the moment, the tools support two deployment architectures:- 
- [Installation on a single server](#install-on-a-single-server)
- [Installation on multiple servers](#install-on-multiple-servers)

You can also do a hybrid of both. [Read more on Architectures](./docs/Deployment-Architectures.md)
## Installation with LXD containers
### Step 0 — Before you start
Ensure you have:
- Linux server, minimum 4GB RAM, 2CPU cores
  - Ubuntu 22.04 or
  - Ubuntu 24.04 
- SSH Access to the server
- A non-root user with sudo privileges.

### Step 1 — SSH to your server (where you want to install DHIS2) and enable firewall. 
- SSH to your server, Secure/harden SSH, allow SSH port on the firewall and
  finally enable the firewall. Be careful not to lock yourself out. Remember to
  allow your preferred ssh port before enabling the firewall. 
  ```
  sudo ufw limit 22 # Assuming you did not change default ssh port (22)
  sudo ufw enable
  ```

### Step 2 — Grab the deployment tools from github
- Access the server and clone the deployment tools in your preferred directory by invoking below command
  ```
  git clone https://github.com/dhis2/dhis2-server-tools.git
  ```

### Step 3 —  Create inventory hosts file
- Create the `hosts` file using the already existing template,
  `hosts.template`. <br>
  Use the command below if you are in the directory you cloned the tools in.
  ```
  cp dhis2-server-tools/deploy/inventory/{hosts.template,hosts}
  ```

### Step 4 — Set fqdn, email, and timezone
- Edit `dhis2-server-tools/deploy/inventory/hosts` file and set `fqdn`, and `email`
  if you have any (you can leave them empty if you do not have).
- Set your preferred `timezone`, you can leave other settings to their set defaults. 
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  Below is an example screenshot
![](./docs/images/fqdn-mail-tz-lxd.png?raw=true "ansible_connection")

  _**NOTE**: When the installation is on a single host with LXD, ensure your lxd_network is unique and not overlapping with any of your host network._ 

###  Step 5 — The Install
- Run `deploy.sh` script from within `dhis2-server-tools/deploy/` directory. 
  ```
  cd dhis2-server-tools/deploy/
  sudo ./deploy.sh
  ```
- After the script finishes running (without errors), access your dhis2, glowroot and munin monitoring instances with your domain (fqdn) set in [Step 5 — The
  Install](#step-5--the-install). If your setup is without fqdn, use your servers' IP address<br>
  ```
  https://your-domain/dhis
  https://your-domain/dhis-glowroot
  https://your-domain/munin
  ```

## Install on physical/virtual servers.
### Step 0: Before you start, make sure you have the following:
- A deployment server - This server is going to your an ansible-controller.<br>DHIS2
  setup on the backend application server will be done from here. We will be using
  deployment server and ansible-controller interchangeably in this guide. 
  - It should run either Ubuntu 22.04 or 24.04 
  - It should have working and tested SSH access to the managed hosts (backend
    application servers). SSH key-based authentication is advisable<br> 
    Deployment will be working with SSH connection. 

    ![](./docs/images/distributed-architecture.png?raw=true "Distributed")
- Backend Servers (managed hosts) - These are the servers that will be running
  your DHIS2 components, i.e database(PostgreSQL, DHIS2, Monitoring, Proxy)
  - They all should be be running Ubuntu 22.04 or 24.04 
  - Be accessible (via ssh) from the deployment server.

### Step 1: Access deployment server (ansible-controller) via SSH 
- SSH to the ansible-controller, Secure/Harden ssh, allow SSH port on the firewall,
  and finally enable the firewall. Be careful not to lock yourself out.
  Remember to allow your preferred SSH port before enabling the firewall.

  ```
  sudo ufw limit 22 #  # Assuming you did not change default SSH port (22)
  sudo ufw enable
  ```

### Step 2: Install ansible on the deployment server
  ```
  sudo apt -y update
  sudo apt install -y  software-properties-common
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -y ansible
  ```

### Step 3: Grab deployment tools from github
-  Access the server and clone the deployment tools in your preferred directory by invoking below command 
  ```
  git clone https://github.com/dhis2/dhis2-server-tools
  ```

### Step 4: Create hosts file (from the hosts template) 
- Create the hosts file using the already existing template, hosts.template.
  Use the command below if you are in the directory you cloned the tools in.
  ```
  cp dhis2-server-tools/deploy/inventory/{hosts.template,hosts}
  ```

### Step 5: Set fqdn, email, timezone and `ansible_connection=ssh` 
- If you do **_NOT_** have a `fqdn`, only set `ansible_connection=ssh`  and
  `timezone`, leave the other variables to their defaults.  
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ![](./docs/images/fqdn-mail-tz-ssh.png?raw=true "ansible_connection")

### Step 6:  Ensure connection to the managed hosts works
- [Read More on how you can configure SSH](./docs/SSH-Connection.md)
- You will need to setup SSH connection from your deployment server to your backend application
servers. 
- Both password or key-based authentication would work. Key-based authentication
  is encouraged if you want your deployment to run fully automated (no prompts
  for SSH passwords). Use ansible ping module to test your connection to all the
  backend hosts except localhost (127.0.0.1)

  ```
  cd dhis2-server-tools/deploy/
  ansible 'all:!127.0.0.1' -m ping 
  ```
  If your SSH connection is successful, you will see SUCCESS messages (as shown in the screenshot below)
  ![](./docs/images/ping_pong.png?raw=true "ping pong")
  
### Step 7: Run the playbook
- Since installing packages on the remote server needs sudo, you will be using `-K` or `--ask-become-pass` 
  ```
  cd dhis2-server-tools/deploy/
  ansible-playbook dhis2.yml -u=username  --ask-become-pass --ask-pass
  ```
<table>
<tr>
    <th style="text-align: left; vertical-align: top;">Description</th>
  </tr>
  <td>
  <code>-k or --ask-pass </code><span>&#8212;</span> prompts for SSH password <br>
  <code>-K or --ask-become-pass</code>&#8212;</span> enables sudo password prompt, you can set <code>ansible_sudo_pass=STRONG_PASSWORD</code> to avoid prompts <br>
  <code>-u</code><span>&#8212;</span> username for SSH connection </td> </tr>
</table>

NOTE:
- When your SSH connection is based on keys, there's no need for the `-k` flag
- If you don't specify an SSH username, it will automatically use currently logged in username.

- After the script finishes running (without errors), access your dhis2,
  glowroot and munin monitoring instances with your domain (fqdn) set in [Step 5 — The
  Install](#step-5--the-install). If your setup is without
  fqdn, use your servers' IP address<br>
  ```
  https://your-domain/dhis
  https://your-domain/dhis-glowroot
  https://your-domain/munin
  ```

## Adding a new instance 
- Edit the inventory hosts file by running the command below and add an entry line under `[instances]`
  category, ensure the instance name and the value of `ansible_host` (instance private IP) are unique. 
  ```
  vim dhis2-server-tools/deploy/inventory/hosts 
  ```
- Example
  ```
  [instances]
  training  ansible_host=172.19.2.12 database_host=postgres  dhis2_version=2.39
  ```
  ![](./docs/images/adding_instance.png?raw=true "customssl")

- re-run the installation as explained on [Step 5 — The
  Install](#step-5--the-install) or [Step 7: Run the
  playbook](#step-7-run-the-playbook) depending on your deployment
  architecture. 

## Using a Custom TLS Certificate 

- Your will need to have two files, named  `customssl.crt` and `customssl.key` <br>
  `customssl.crt` should contain the main certificate concatenated with intermediate and
   root certificates.
-  Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory, preserving their names.
- Edit hosts file and set `TLS_TYPE=customssl`
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ![](./docs/images/ssl_type.png?raw=true "customssl")
- re-run the installation as explained on [Step 5 — The
  Install](#step-5--the-install) or [Step 7: Run the
  playbook](#step-7-run-the-playbook) depending on your deployment
  architecture. 

## Conclusion
- At this point you should have dhis2 up and running. Let's assume your DHIS2
  application is named dhis
  - https://your-domain|server-ip-address/dhis<br>
    Logins: Username: admin Password: district

- In addition, the tools will also setup [glowroot](https://glowroot.org/), an open
  source APM (Application Performance Monitoring) for Java-based applications, to monitor the performance of our DHIS2 application
  - https://your-domain|ip-address/dhis-glowroot<br> 
    Logins: Username: admin Password: district

- Server monitoring is also setup with
  [munin](https://munin-monitoring.org/) <br>
  - Url: https://your-domain|server-ip-address/munin<br>
    If you changed munin_base_path variable<br>
    URL: https://your-domain|server-ip-address/your_munin_base_path <br>
    Logins: Username: admin Password: district


## Other important links 
- [Supported variables ](./docs/Variables.md)
- [Hosts and hosts grouping ](./docs/Inventory-Host-File.md)
- [Optimizing PostgreSQL](./docs/Optimizing-PostgreSQL.md)
- [LXC container management](./docs/Basic-LXC-container-Management.md)
- [Service management with systemctl](./docs/Systemd-Service-Management.md)
- [SSH connection](./docs/SSH-Connection.md)
