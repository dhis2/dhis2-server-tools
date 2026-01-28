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
	* [Step 1: Before you start, make sure you have the following:](#step-1-before-you-start-make-sure-you-have-the-following)
	* [Step 2: Access deployment server (ansible-controller) via SSH](#step-2-access-deployment-server-ansible-controller-via-ssh)
	* [Step 3: Install ansible on the deployment server](#step-3-install-ansible-on-the-deployment-server)
	* [Step 4: Grab deployment tools from github](#step-4-grab-deployment-tools-from-github)
	* [Step 5: Create hosts file (from the hosts template)](#step-5-create-hosts-file-from-the-hosts-template)
	* [Step 6: Set fqdn, email, timezone and `ansible_connection=ssh`](#step-6-set-fqdn-email-timezone-and-ansible_connectionssh)
	* [Step 7:  Ensure connection to the managed hosts works](#step-7--ensure-connection-to-the-managed-hosts-works)
	* [Step 8: Run the playbook](#step-8-run-the-playbook)
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

At the moment, the tools support two deployment architectures:
- [Installation with LXD containers](#installation-with-lxd-containers) (single server)
- [Installation on physical/virtual servers](#install-on-physicalvirtual-servers) (multiple servers)

You can also do a hybrid of both. [Read more on Architectures](./docs/Deployment-Architectures.md)

## Installation with LXD containers
### Step 0 — Before you start
Ensure you have:
- Linux server, minimum 4GB RAM, 2 CPU cores
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
```ini
# variables applying to all hosts,
[all:vars]
# if you do not set fqdn, you dhis2 will be set up with self-signed certificate
fqdn=your-domain.example.com
# required for LetsEncrypt certificate notification.
email=your-email@example.com
# timedatectl list-timezones to list timezones
# Example: timezone=Africa/Nairobi
timezone=your-timezone
# Options: lxd, ssh defaults to lxd.
ansible_connection=lxd
```

  _**NOTE**: When the installation is on a single host with LXD, ensure your lxd_network is unique and not overlapping with any of your host network._ 

###  Step 5 — The Install
- Run `deploy.sh` script from within `dhis2-server-tools/deploy/` directory. 
  ```
  cd dhis2-server-tools/deploy/
  sudo ./deploy.sh
  ```
- After the script finishes running (without errors), access your DHIS2, Glowroot and Munin monitoring instances:
  > **Note:** `<hostname>` = your `fqdn` if defined, otherwise your server's IP address.
  ```
  https://<hostname>/dhis
  https://<hostname>/dhis-glowroot
  https://<hostname>/munin
  ```

## Install on physical/virtual servers.
### Step 1: Before you start, make sure you have the following:
- A deployment server - This server is going to be your ansible-controller.<br>DHIS2
  setup on the backend application server will be done from here. We will be using
  deployment server and ansible-controller interchangeably in this guide. 
  - It should run either Ubuntu 22.04 or 24.04 
  - It should have working and tested SSH access to the managed hosts (backend
    application servers). SSH key-based authentication is advisable<br> 
    Deployment will be working with SSH connection. 

    ```mermaid
    graph LR
        A[Deployment Server<br/>Ansible Controller] -->|ssh| B[Database Server<br/>PostgreSQL]
        A -->|ssh| C[DHIS2<br/>Application Server]
        A -->|ssh| D[Proxy<br/>Nginx/Apache2]
        A -->|ssh| E[Monitoring Server<br/>Munin]
        F["./inventory/<br/>- hosts<br/>- group_vars<br/>- host_vars"] -.-> A
        subgraph Managed Hosts
            B
            C
            D
            E
        end
    ```
- Backend Servers (managed hosts) - These are the servers that will be running
  your DHIS2 components, i.e database(PostgreSQL, DHIS2, Monitoring, Proxy)
  - They all should be running Ubuntu 22.04 or 24.04 
  - Be accessible (via ssh) from the deployment server.

### Step 2: Access deployment server (ansible-controller) via SSH 
- SSH to the ansible-controller, Secure/Harden ssh, allow SSH port on the firewall,
  and finally enable the firewall. Be careful not to lock yourself out.
  Remember to allow your preferred SSH port before enabling the firewall.

  ```
  sudo ufw limit 22 # Assuming you did not change default SSH port (22)
  sudo ufw enable
  ```

### Step 3: Install ansible on the deployment server
  ```
  sudo apt -y update
  sudo apt install -y software-properties-common
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -y ansible
  ```

### Step 4: Grab deployment tools from github
-  Access the server and clone the deployment tools in your preferred directory by invoking below command 
  ```
  git clone https://github.com/dhis2/dhis2-server-tools
  ```

### Step 5: Create hosts file (from the hosts template) 
- Create the hosts file using the already existing template, hosts.template.
  Use the command below if you are in the directory you cloned the tools in.
  ```
  cp dhis2-server-tools/deploy/inventory/{hosts.template,hosts}
  ```

### Step 6: Set fqdn, email, timezone and `ansible_connection=ssh`
- Edit the inventory hosts file and configure the following variables:
  - `fqdn` — your domain name. Leave empty if you don't have one (DHIS2 will use a self-signed certificate)
  - `email` — for LetsEncrypt certificate notifications
  - `timezone` — use `timedatectl list-timezones` to list available options
  - `ansible_connection=ssh` — **required** for physical/virtual server deployments
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ```ini
  # variables applying to all hosts,
  [all:vars]
  # if you do not set fqdn, you dhis2 will be set up with self-signed certificate
  fqdn=your-domain.example.com
  # required for LetsEncrypt certificate notification.
  email=your-email@example.com
  # timedatectl list-timezones to list timezones
  # Example: timezone=Africa/Nairobi
  timezone=your-timezone
  # Options: lxd, ssh defaults to lxd.
  ansible_connection=ssh
  ```

### Step 7:  Ensure connection to the managed hosts works
- [Read More on how you can configure SSH](./docs/SSH-Connection.md)
- You will need to setup SSH connection from your deployment server to your backend application servers. 
- Both password or key-based authentication would work. Key-based authentication
  is encouraged if you want your deployment to run fully automated (no prompts
  for SSH passwords). Use ansible ping module to test your connection to all the
  backend hosts except localhost (127.0.0.1)

  ```
  cd dhis2-server-tools/deploy/
  ansible 'all:!127.0.0.1' -m ping 
  ```
  If your SSH connection is successful, you will see SUCCESS messages like below:
  ```json
  dhis | SUCCESS => {
      "ansible_facts": {
          "discovered_interpreter_python": "/usr/bin/python3"
      },
      "changed": false,
      "ping": "pong"
  }
  monitor | SUCCESS => {
      "ansible_facts": {
          "discovered_interpreter_python": "/usr/bin/python3"
      },
      "changed": false,
      "ping": "pong"
  }
  ```
  
### Step 8: Run the playbook
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
  <code>-K or --ask-become-pass</code><span>&#8212;</span> enables sudo password prompt, you can set <code>ansible_sudo_pass=STRONG_PASSWORD</code> to avoid prompts <br>
  <code>-u</code><span>&#8212;</span> username for SSH connection </td> </tr>
</table>

NOTE:
- When your SSH connection is based on keys, there's no need for the `-k` flag
- If you don't specify an SSH username, it will automatically use currently logged in username.

- After the playbook finishes running (without errors), access your DHIS2, Glowroot and Munin monitoring instances:
  > **Note:** `<hostname>` = your `fqdn` if defined, otherwise your server's IP address.
  ```
  https://<hostname>/dhis
  https://<hostname>/dhis-glowroot
  https://<hostname>/munin
  ```

## Adding a new instance 
- Edit the inventory hosts file by running the command below and add an entry line under `[instances]`
  category, ensure the instance name and the value of `ansible_host` (instance private IP) are unique. 
  ```
  vim dhis2-server-tools/deploy/inventory/hosts 
  ```
- Example
  ```ini
  [web]
  proxy  ansible_host=172.19.2.2

  # database servers/containers
  [databases]
  postgres  ansible_host=172.19.1.20

  # dhis2 servers/containers
  [instances]
  hmis      ansible_host=172.19.2.11  database_host=postgres  dhis2_version=2.39 proxy_rewrite=True
  training  ansible_host=172.19.2.12  database_host=postgres  dhis2_version=2.39
  # <-- add new instance here

  # monitoring server/container
  [monitoring]
  monitor   ansible_host=172.19.2.30
  ```

- re-run the installation as explained on [Step 5 — The
  Install](#step-5--the-install) or [Step 7: Run the
  playbook](#step-8-run-the-playbook) depending on your deployment
  architecture. 

## Using a Custom TLS Certificate 

- You will need to have two files, named `customssl.crt` and `customssl.key`.<br>
  `customssl.crt` should contain the main certificate concatenated with intermediate and
   root certificates.
-  Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory, preserving their names.
- Edit hosts file and set `TLS_TYPE=customssl`
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ```ini
  # Options: nginx, apache2 defaults to nginx
  proxy=nginx

  # Options: letsencrypt, customssl, default(letsencrypt)
  SSL_TYPE=customssl
  ```
- re-run the installation as explained on [Step 5 — The
  Install](#step-5--the-install) or [Step 7: Run the
  playbook](#step-8-run-the-playbook) depending on your deployment
  architecture. 

## Conclusion
At this point you should have DHIS2 up and running.

> **Note:** `<hostname>` = your `fqdn` if defined, otherwise your server's IP address.

- **DHIS2** — `https://<hostname>/dhis`
- **Glowroot** — `https://<hostname>/dhis-glowroot` ([glowroot.org](https://glowroot.org/) for application performance monitoring)
- **Munin** — `https://<hostname>/munin` ([munin-monitoring.org](https://munin-monitoring.org/) for server resource monitoring)
  - If you changed `munin_base_path`: `https://<hostname>/<your_munin_base_path>`

> **Default credentials:** Username: `admin` / Password: `district`
>
> **Important:** Change these default passwords immediately after your first login.


## Other important links 
- [Supported variables ](./docs/Variables.md)
- [Hosts and hosts grouping ](./docs/Inventory-Host-File.md)
- [Optimizing PostgreSQL](./docs/Optimizing-PostgreSQL.md)
- [LXC container management](./docs/Basic-LXC-container-Management.md)
- [Service management with systemctl](./docs/Systemd-Service-Management.md)
- [SSH connection](./docs/SSH-Connection.md)
