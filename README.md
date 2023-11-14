Table of contents
---
<!-- vim-markdown-toc GFM -->

* [Introduction](#introduction)
* [Install on a single server](#install-on-a-single-server)
	* [Step 0 — Before you start](#step-0--before-you-start)
	* [Step 1 — SSH to your server and enable firewall.](#step-1--ssh-to-your-server-and-enable-firewall)
	* [Step 2 — Grab deployment tools from github](#step-2--grab-deployment-tools-from-github)
	* [Step 3 —  Create hosts file](#step-3---create-hosts-file)
	* [Step 4 — Set fqdn, email,timezone](#step-4--set-fqdn-emailtimezone)
	* [Step 5 — The Install](#step-5--the-install)
* [Install on multiple servers](#install-on-multiple-servers)
	* [Step 0: Before you start](#step-0-before-you-start)
	* [Step 1: Access deployment server (ansible controller) via ssh](#step-1-access-deployment-server-ansible-controller-via-ssh)
	* [Step 2: Install ansible on the deployment server](#step-2-install-ansible-on-the-deployment-server)
	* [Step 3: Grab deployment tools from github](#step-3-grab-deployment-tools-from-github)
	* [Step 4: Create hosts file (from the hosts template)](#step-4-create-hosts-file-from-the-hosts-template)
	* [Step 5: Set fqdn, email,timezone and `ansible_connection=ssh`](#step-5-set-fqdn-emailtimezone-and-ansible_connectionssh)
	* [Step 6:  Ensure connection to the managed hosts works](#step-6--ensure-connection-to-the-managed-hosts-works)
	* [Step 7: Run the playbook](#step-7-run-the-playbook)
* [Adding an instance](#adding-an-instance)
* [Using a Custom SSL Certificate](#using-a-custom-ssl-certificate)
* [Conclusion](#conclusion)
* [other important links](#other-important-links)

<!-- vim-markdown-toc -->
---

## Introduction 
This is a quick DHIS2 install guide using [ansible](https://www.ansible.com/). At the end, you will have
one or more dhis2 instances running, configured with postgreSQL database and
nginx or apache2 proxy. You will have munin server monitoring as well. 

At the moment, the tools support two deployment architectures:- 
- [Install on a single server](#install-on-a-single-server)
- [Install on multiple servers](#install-on-multiple-servers)

You can also do a hybrid of both. [Read more on Architectures](./docs/Deployment-Architectures.md)
## Install on a single server
### Step 0 — Before you start
Ensure you have:
- Linux server, minimum 4GB RAM, 2CPU cores
  - Ubuntu 20.04 or
  - Ubuntu 22.04 
- SSH Access to the server
- A non-root user with sudo privileges.

### Step 1 — SSH to your server and enable firewall. 
- SSH to your server, secure your ssh, allow ssh port on the firewall and
  finally enable the firewall. Be careful not to lock yourself out. Remember to
  allow ssh port before enabling the firewall. 
  ```
  sudo ufw limit 22 # Assuming you did not change default ssh port 22
  sudo ufw enable
  ```

### Step 2 — Grab deployment tools from github
- Access the server and get deployment tools by invoking below command
  ```
  git clone https://github.com/dhis2/dhis2-server-tools
  ```

### Step 3 —  Create hosts file
- Create the `hosts` file using the already existing template,
  `hosts.template`. <br>
  Use command below 
  ```
  cp dhis2-server-tools/deploy/inventory/{hosts.template,hosts}
  ```

### Step 4 — Set fqdn, email,timezone
- Edit `dhis2-server-tools/deploy/inventory/hosts` file and set `fqdn`, `email`
  if you have.(you can leave them empty if you do not have)
- Set your preferred `timezone`, you can leave other settings to their set defaults. 

  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  Below is an example screenshot
![Alt text](./docs/images/fqdn-mail-tz-lxd.png?raw=true "ansible_connection")

  _**NOTE**: When the install is on a single host with lxd, ensure your lxd_network is unique and not overlapping with any of your host network._ 

###  Step 5 — The Install
- Run `deploy.sh` script from withing `dhis2-server-tools/deploy/` directory. 
  ```
  cd dhis2-server-tools/deploy/
  sudo ./deploy.sh
  ```
- After the script finishes running (without errors), access your dhis2, glowroot and munin monitoring with your domain. If your setup is without fqdn, use servers ip address<br>
  ```
  https://your-domain/dhis
  https://your-domain/dhis-glowroot
  https://your-domain/munin
  ```

## Install on multiple servers
### Step 0: Before you start
- A deployment server - This server is going to an ansible-controller.<br>DHIS2
  setup on the backend server will done from here. I will be using
  deployment server and ansible-controller interchangeably in this tutorial. 
  -  It should runs either Ubuntu 20.04 or 22.04 
  - It should have working and tested ssh access to the managed hosts (backend
    application servers). Key based authentication is advisable<br> 
    Deployment will be working with ssh connection. 

    ![Alt text](./docs/images/distributed-architecture.png?raw=true "Distributed")
- Backend Servers (managed hosts) - These are the servers that will be running
  your DHIS2 components, i.e database(PostgreSQL,DHIS2,Monitoring,Proxy)
  - They all should be be running Ubuntu 20.04 or 22.04 
  - Be accessible (via ssh) from the deployment server.

### Step 1: Access deployment server (ansible controller) via ssh 
- SSH to the ansible-controller , secure ssh, allow ssh port on the firewall,
  and finally enable the firewall. Be careful not to lock yourself out.
  Remember to allow ssh port before enabling the firewall.

  ```
  sudo ufw limit 22 #  # Assuming you did not change default ssh port 22
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
- After accessing deployment server, download install tools from github 
  ```
  git clone https://github.com/dhis2/dhis2-server-tools
  ```

### Step 4: Create hosts file (from the hosts template) 
- Create the hosts file using the already existing template, hosts.template.
  Use command below
  ```
  cp dhis2-server-tools/deploy/inventory/{hosts.template,hosts}
  ```

### Step 5: Set fqdn, email,timezone and `ansible_connection=ssh` 
- If you do **_NOT_** have `fqdn` only set `ansible_connection=ssh`  and
  `timezone`, leave other variables to their defaults.  
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ![Alt text](./docs/images/fqdn-mail-tz-ssh.png?raw=true "ansible_connection")

### Step 6:  Ensure connection to the managed hosts works
- [Read More on how you can configure ssh](./docs/SSH-Connection.md)
- You will need to setup ssh connection from deployment server to you backend
servers. 
- Both password or key-based authentication can work. Key-based authentication
  is encouraged if you want your deployment to run fully automated (no prompts
  for ssh passwords). Use ansible ping module to test your connection to all the
  backend hosts except localhost (127.0.0.1)

  ```
  cd dhis2-server-tools/deploy/
  ansible 'all:!127.0.0.1' -m ping 
  ```
  If your ssh is working, you will see SUCCESS messages as show on below screenshot
  ![Alt text](./docs/images/ping_pong.png?raw=true "ping pong")
  
### Step 7: Run the playbook
- Since installing packages on the remote needs sudo, you will be using `-K` or `--ask-bocome-pass` 
  ```
  cd dhis2-server-tools/deploy/
  ansible-playbook dhis2.yml -u=username  --ask-become-pass --ask-pass
  ```
<table>
<tr>
    <th style="text-align: left; vertical-align: top;">Description</th>
  </tr>
  <td>
  <code>-k or --ask-pass </code><span>&#8212;</span> prompts for ssh password <br>
  <code>-K or --ask-become-pass</code>&#8212;</span> enables sudo password prompt, you can set <code>ansible_sudo_pass=STRONG_PASSWORD</code> and avoid prompts <br>
  <code>-u</code><span>&#8212;</span> username for ssh connection </td> </tr>
</table>

NOTE:
- When your SSH connection is based on keys, there's no need for the `-k` flag
- If you don't specify an SSH username, it will automatically use currently logged in username.

- After the script finishes running (without errors), access your dhis2,
  glowroot and munin monitoring with your domain. If your setup is without
  fqdn, use servers ip address<br>
  ```
  https://your-domain/dhis
  https://your-domain/dhis-glowroot
  https://your-domain/munin
  ```

## Adding an instance 
- Edit inventory hosts file, and add an entry line under `[instances]`
  category, ensure the name and `ansible_host` are unique. 
  ```
  vim dhis2-server-tools/deploy/inventory/hosts 
  ```
- Example
  ```
  [instances]
  training  ansible_host=172.19.2.12 database_host=postgres  dhis2_version=2.39
  ```
  On the above example,  the name `training` and `ansible_host`  should be  to be unique. 
  ![Alt text](./docs/images/adding_instance.png?raw=true "customssl")

- re-run the installation as explained on [Step 5 — The
  Install](#step-5--the-install) or [Step 7: Run the
  playbook](#step-7-run-the-playbook) depending on your deployment
  architecture. 

## Using a Custom SSL Certificate 

- Your will need to have two files, named  `customssl.crt` and `customssl.key` <br>
  `customssl.crt` should contain main certificate concatenated with intermediate and
   root certificates.
-  Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory, preserving their names.
- Edit hosts file and set `SSL_TYPE=customssl`
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ![Alt text](./docs/images/ssl_type.png?raw=true "customssl")
- re-run the installation as explained on [Step 5 — The
  Install](#step-5--the-install) or [Step 7: Run the
  playbook](#step-7-run-the-playbook) depending on your deployment
  architecture. 

## Conclusion
- At this point you would have dhis2 up and running. Lets assume you DHIS2
  application is named dhis
  - https://your-domain|ip-address/dhis<br>
    Logins: Username: admin Password: district

- In addition, the tools will setup [glowroot](https://glowroot.org/) an open
  source APM tool for Java App monitoring
  - https://your-domain|ip-address/dhis-glowroot<br> 
    Logins: Username: admin Password: district

- Server monitoring will be configured with
  [munin](https://munin-monitoring.org/) <br>
  - Url: https://your-domain|ip-address/munin<br>
    If you changed munin_base_path variable<br>
    URL: https://your-domain|ip-address/your_munin_base_path <br>
    Logins: Username: admin Password: district


## other important links 
- [Supported Variables ](./docs/Variables.md)
- [hosts and hosts grouping ](./docs/Inventory-Host-File.md)
- [Optimizing PostgreSQL](./docs/Optimizing-PostgreSQL.md)
- [lxc container management](./docs/Basic-LXC-container-Management.md)
- [service management with systemctl](./docs/Systemd-Service-Management.md)
