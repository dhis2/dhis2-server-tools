Table of contents
---
<!-- vim-markdown-toc GFM -->

* [Introduction](#introduction)
* [Quick before you start](#quick-before-you-start)
* [Step 1 — SSH to your server and enable host firewall with UFW](#step-1--ssh-to-your-server-and-enable-host-firewall-with-ufw)
* [Step 2 — Grab deployment tools from github](#step-2--grab-deployment-tools-from-github)
* [Step 3 —  Create hosts file](#step-3---create-hosts-file)
* [Step 4 — Set fqdn, email,timezone and ansible_connection.](#step-4--set-fqdn-emailtimezone-and-ansible_connection)
* [Step 5 — The Install](#step-5--the-install)
	* [On a single server](#on-a-single-server)
	* [On multiple servers](#on-multiple-servers)
* [Adding an instance](#adding-an-instance)
* [Using a Custom SSL Certificate](#using-a-custom-ssl-certificate)
* [Monitoring](#monitoring)
* [other important links](#other-important-links)

<!-- vim-markdown-toc -->
---

## Introduction 

This is a quick DHIS2 install guide using ansible. At the end, you will have
one or more dhis2 instances running, configured with postgreSQL database and
nginx or apache2 proxy. You will have munin server monitoring as well. 

At the moment, the tools support two deployment architectures, i.e single
server with LXD Containers and Multiple Server. You can also do a hybrid of
both. [Read more on Architectures](./docs/Deployment-Architectures.md)

## Quick before you start
Ensure you have:
* Linux server, minimum 4GB RAM, 2CPU cores
  * Ubuntu 20.04 or
  * Ubuntu 22.04 
* SSH Access to the server
* A non-root user with sudo privileges.

## Step 1 — SSH to your server and enable host firewall with UFW
SSH to your server, secure your ssh, and enable the firewall. Be careful not to
lock yourself out. Remember to allow ssh port before enabling the firewall. 
```
ssh username@ip-address -p ssh-port
sudo ufw limit 22 # can be different if you are using non default ssh port
sudo ufw enable

```
## Step 2 — Grab deployment tools from github
Access the server and get deployment tools by invoking below command
```
git clone https://github.com/dhis2/dhis2-server-tools
```
   

## Step 3 —  Create hosts file
Create the `hosts` file using the already existing template, `hosts.template`.
Use below command. 

```
cp dhis2-server-tools/deploy/inventory/{hosts.template,hosts}
```

At this point your can already run install script. 
That will install dhis2 on the server without domain name and you'll be
accessing the app with the server's ip address. However, in a prod setup,
you'll usually need a fully qualified domain name (fqdn) 

## Step 4 — Set fqdn, email,timezone and ansible_connection.
If you do not have the domain name (fqdn) skip to  [Step 5 — The Install](#step-5--the-install), otherwise edit
`hosts` file and set `fqdn`, `email` and `timezone` you can
leave other settings to their set defaults. 

```
vim dhis2-server-tools/deploy/inventory/hosts
```
Below is an example screenshot

![Alt text](./docs/images/fqdn-mail-tz.png?raw=true "Sample Screenshot")

_**NOTE**: When the install is on a single host with lxd, ensure your
lxd_network is unique and not overlapping with any of your host network._ 

##  Step 5 — The Install
### On a single server
Run `deploy.sh` script from withing `dhis2-server-tools/deploy/` directory. 

```
cd dhis2-server-tools/deploy/
sudo ./deploy.sh
```

### On multiple servers
Prerequisite for distributed setup
* A deployment server to be used as an ansible controller. 
  * Runs either Ubuntu 20.04 or 22.04 
  * have ansible version 2.11 or newer installed<br>
    install ansible with below script
    ```
    sudo apt -y update
    sudo apt install -y  software-properties-common
    sudo apt-add-repository --yes --update ppa:ansible/ansible
    sudo apt install -y ansible
    ```
  * working ssh access to the managed hosts. Key based authentication is advisable<br> 
    Deployment will be working with ssh connection. 


* Set `ansible_connection=ssh` by editing inventory file. 
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ![Alt text](./docs/images/ansible_connection.png?raw=true "ansible_connection")

* Run the playbook
  ```
  cd dhis2-server-tools/deploy/
  ansible-playbook dhis2.yml -u=username -Kk 
  ```
<table>
<tr>
    <th style="text-align: left; vertical-align: top;">Description</th>
  </tr> <td><code>-K</code>&#8212;</span> enables sudo password prompt, you can set <code>ansible_sudo_pass=STRONG_PASSWORD</code> and avoid prompts<br><code>-k</code><span>&#8212;</span> prompts for ssh password <br><code>-u</code><span>&#8212;</span> username for ssh connection </td> </tr>
</table>

NOTE:
* When your SSH connection is based on keys, there's no need for the `-k` flag
* If you don't specify an SSH username, it will automatically use your $USER as the default.

![Alt text](./docs/images/distributed-architecture.png?raw=true "Distributed")
<!-- ## Step 6 — Accessing the instances -->
<!-- You can access the instance with your configured ip address, --> 
<!-- * https://yourdomain/instance-name - to access the instance --> 
<!-- * https://yourdoomain/instance-glowrtoot to access glowroot -->
<!-- * https://yourdomain/munin	  - to access munin monitoring tool --> 
## Adding an instance 
Edit inventory hosts file, and add an entry line under `[instances]` category,
ensure the name and `ansible_host` are unique. 

Then re-run `install.sh` script as its is explained on [On a single server](#on-a-single-server). 

```
vim dhis2-server-tools/deploy/inventory/hosts 
```

Example
```
[instances]
training  ansible_host=172.19.2.12 database_host=postgres  dhis2_version=2.39
```
On the above example,  the name `training` and `ansible_host`  should be  to be unique. 

## Using a Custom SSL Certificate 

* Your will need to have two files, named  `customssl.crt` and `customssl.key` <br>
  `customssl.crt` should contain main certificate concatenated with intermediate and
   root certificates.
*  Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory, preserving their names.
* Edit hosts file and set `SSL_TYPE=customssl`
  ```
  vim dhis2-server-tools/deploy/inventory/hosts
  ```
  ![Alt text](./docs/images/ssl_type.png?raw=true "customssl")
## Monitoring
By default the script implements monitoring with munin and glowroot. Munin is
for server monitoring whereas glowroot is for tomcat application monitoring and profiling.  

You can access munin on https://fqdn/munin and glowroot is available on
https://fqdn/app_name-glowroot where app_name is your running dhis2
instances name. 

By default, munin and glowroot are configured with default logins, username:
admin and password: district which you can change after the install. 

## other important links 
- [Supported Variables ](./docs/Variables.md)
- [hosts and hosts grouping ](./docs/Inventory-Host-File.md)
- [Optimizing PostgreSQL](./docs/Optimizing-PostgreSQL.md)
- [lxc container management](./docs/Basic-LXC-container-Management.md)
- [service management with systemctl](./docs/Systemd-Service-Management.md)
