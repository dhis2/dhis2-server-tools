## Introduction 

In this repository, you'll find Ansible playbooks and roles designed to
automate the installation and configuration of the DHIS2 application. The
ultimate objective is to set up all the components of the DHIS2 stack,
including the Java web app, PostgreSQL, proxy and monitoring tools. 

With these tools, we strive to support various deployment architectures, i.e single server
(boombox), distributed and a hybrid. [Read more on Architectures](./docs/Deployment-Architectures.md)

---
<!-- vim-markdown-toc GFM -->

* [Requirements before you start](#requirements-before-you-start)
* [Install ansible version 2.11 or newer](#install-ansible-version-211-or-newer)
* [Grab deployment tools for git](#grab-deployment-tools-for-git)
* [Create an inventory file from hosts.template file](#create-an-inventory-file-from-hoststemplate-file)
* [Customization before installation](#customization-before-installation)
  * [Read more on  supported variables](#read-more-on--supported-variables)
  * [Read more on hosts grouping](#read-more-on-hosts-grouping)
* [Running ansible playbook | Installation](#running-ansible-playbook--installation)
  * [Install on single server](#install-on-single-server)
  * [Install distributed architecture](#install-distributed-architecture)
* [Using a Custom SSL Certificate](#using-a-custom-ssl-certificate)
  * [Steps to configure customssl support](#steps-to-configure-customssl-support)
* [adding another dhis2 instance](#adding-another-dhis2-instance)
* [Optimizing Postgresql](#optimizing-postgresql)
* [lxc container management](#lxc-container-management)
* [service management with systemctl](#service-management-with-systemctl)
* [Monitoring](#monitoring)

<!-- vim-markdown-toc -->
---

## Requirements before you start
* Ubuntu server running 20.04 or 22.04. 
* ssh access to the server. 
* non root user with sudo. 

## Install ansible version 2.11 or newer

  _**NOTE:** For a [distributed
architecture](./docs/Deployment-Architectures.md#distributed-architecture) ,
you'll need a separate deployment server, with working ssh access to all
managed servers._
  If you are doing installation on Ubuntu 18.04, use pip3 to install latest for ansible version
  Run below commands to install ansible 
  ```
  sudo apt -y update
  sudo apt install -y  software-properties-common
  sudo apt-add-repository --yes --update ppa:ansible/ansible
  sudo apt install -y ansible
  sudo apt-get install -y python3-netaddr
  ```
  Install community.general ansible modules, required for lxd_container, ufw and other modules 
```
ansible-galaxy collection install community.general -f
```

## Grab deployment tools for git
`git clone https://github.com/dhis2/dhis2-server-tools`

## Create an inventory file from hosts.template file
A before doing anything with these tools, you'll need an inventory hosts file.
A good start would be from `hosts.template` file which we ship with the tools. 

Create it by copying`hosts.template` to `hosts`

```
cd dhis2-server-tools/deploy/inventory/
cp hosts.template hosts
```

##  Customization before installation

You will edit `hosts` file and set `fqdn`, `email` and `timezone` you can leave other
settings to their set defaults. 

```
vim dhis2-server-tools/deploy/inventory/hosts
```
<table>
  <tr>
    <th style="text-align: left; vertical-align: top;">Parameter</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td><code>fqdn</code></td>
    <td> This is the domain used to access dhis2 application <br>Strictly required for Letsencrypt  </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>email</code></td>
    <td>Strictly required if you are using Letsencrypt</td>
  </tr>
  <tr>
    <td><code>timezone</code></td>
    <td>list all available <code>timezones</code> with <code>timedatectl
    list-timezones</code>  <br>Examples</strong> <br>
    <ul><li><code>Europe/Oslo</code>
    </li><li><code>Africa/Nairobi</code></li></ul></td>
  </tr>
  <tr>
     <td style="vertical-align: top; text-align: left;"><code>ansible_connection</code></td>
    <td>Depends on the <a
    href="./docs/Deployment-Architectures.md">Architecture</a> you are
    adopting, default is <code>lxd</code> <br> <strong>Options</strong> <br>
    <ul><li>lxd ← (default), for single server architecture </li><li>ssh ←
    Distributed Architecture</li></ul> </td>
  </tr>
</table>

### Read more on [ supported variables](./docs/Variables.md)

_**NOTE**: `When the install is on a single host with lxd, ensure your
lxd_network is unique and not overlapping with any of your host network.`_ 

The host are grouped into categories below, 
<table>
  <tr>
    <th style="text-align: left; vertical-align: top;">Group</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td><code>[proxy]</code></td>
    <td> list of proxy servers  </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>[database]</code></td>
    <td>list of database servers</td>
  </tr>
  <tr>
    <td><code>[instances]</code></td>
    <td> list of dhis2 application servers </td>
  </tr>

  <tr>
     <td style="vertical-align: top; text-align: left;"><code>[monitoring] </code></td>
    <td> monitoring servers </td>
  </tr>
</table>

### Read more on [hosts grouping](./docs/Inventory-Host-File.md#hosts-grouping)

##  Running ansible playbook | Installation
### Install on single server
Its the default supported architecture, you'll be running the tools from the
same single server that you'll have dhis2 setup.
```
sudo ufw limit 22 
sudo ufw enable
cd dhis2-server-tools/deploy/
sudo ./deploy.sh
```
<table>
<tr>
    <th style="text-align: left; vertical-align: top;">Command</th>
    <th style="text-align: left; vertical-align: top;">Description</th>
  </tr>
<tr>
    <td style="vertical-align: top; text-align: left; white-space: nowrap;"><code>sudo ufw limit 22</code><br><code>sudo ufw enable</code></td>
    <td style="white-space: nowrap;">Opens ssh port on the host firewall</td>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left; white-space: nowrap;"><code>cd dhis2-server-tools/deploy/ </code></td>
    <td> cd into dhis2-server-tools/deploy/ directory </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>sudo ./deploy.sh </code></td>
    <td> run the deploy script,  </td>
  </tr>
</table>

### Install distributed architecture
Here you'll be sitting on the deployment server and you have ssh connection to
the hosts to be managed, you'll also have ansible installed.
```
sudo ufw limit 22 
sudo ufw enable
cd dhis2-server-tools/deploy/
vim inventory/hosts 	
ansible-playbook dhis2.yml -u=ssh_username -Kk 
```

<table>
<tr>
    <th style="text-align: left; vertical-align: top;">Command</th>
    <th style="text-align: left; vertical-align: top;">Description</th>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>sudo ufw limit 22</code><br><code>sudo ufw enable</code></td>
    <td> Opens ssh port on the host firewall, change 22 to if you are using non default ssh port </td>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left; white-space: nowrap;"><code>cd dhis2-server-tools/deploy/</code></td>
    <td> cd into dhis2-server-tools/deploy/ directory </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>vim inventory/hosts </code></td>
    <td> Edit inventory hosts file and set <code>ansible_connection=ssh </code> </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code> ansible-playbook dhis2.yml -u=your_ssh_user -Kk </code></td>
    <td><code>-K</code>&#8212;</span> prompts for sudo password <br><code>-k</code><span>&#8212;</span> prompts for ssh password <br><code>-u</code> <span>&#8212;</span> username for ssh connection 
 </td>
  </tr>
</table>

## Using a Custom SSL Certificate 
To use custom ssl certificate, you will change the variable below, i.e <code>SSL_TYPE=customssl</code>
<style>
    table {
        table-layout: fixed;
    }
    th, td {
        white-space: wrap;
    }
</style>
<table>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>SSL_TYPE</code></td>
    <td> This parameter enables to specify whether you'd want to use
    <code>letsencrypt</code> or your own <code>customssl</code>
    certificate, For <code>customssl</code> insure you
    have TLS cert and key before proceeding, <br> <strong>Options</strong> <br> <ul><li>letsencrypt ←
    (default)</li><li>customssl</li></ul> </td>
    </tr>
</table>

### Steps to configure customssl support

1. Your will need to have two files  `customssl.crt` and `customssl.key` files.
   The certificate contains main certificate concatenated with intermediate and
   root certificates.
2. Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory.
3. Edit `dhis2-server-tools/deploy/inventory/hosts` and change `SSL_TYPE`  to `customssl` 
## adding another dhis2 instance 
Edit inventory hosts file 
<table>
<tr>
    <th style="text-align: left; vertical-align: top;">Command</th>
    <th style="text-align: left; vertical-align: top;">Description</th>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>cd dhis2-server-tools/deploy/ </code></td>
    <td> cd into dhis2-server-tools/deploy/ directory </td>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>cd dhis2-server-tools/deploy/</code></td>
    <td> cd into dhis2-server-tools/deploy/ directory </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>vim inventory/hosts  </code></td>
    <td> edit inventory hosts file and add a line under  <code>[instances]</code> hosts group, ensure its unique in terms of the name and ansible_host  </td>
  </tr>
</table>

Example
```
[instances]
dhis  ansible_host=172.19.2.12 database_host=postgres  dhis2_version=2.39
```

## Optimizing Postgresql
The default settings of the installed PostgreSQL database should be sufficient
and functional at this point. However, for performance optimization and to
full utilize the available system resources, you may consider making some
adjustments. To begin with the optimization process, it is essential to first
assess the resources available on your system. I.e, total RAM  available, use
`free -h` for that.

The amount of RAM to allocate to PostgreSQL depends on the number of DHIS2
instances you plan to run. If you have a production instance and a small test
instance, with 32GB of RAM, dedicating 16GB exclusively to PostgreSQL would be
a reasonable starting point.

Decide amount of RAM to allocate PostgreSQL, and limit the postgres container to that size, e.g 
```
sudo lxc config set postgresql limits.memory 16GB
```
PostgreSQL specific parameters can be set for further optimization,
Add a file on dhis2-server-tools/deploy/inventory/host_vars/postgres_host
If for example you database host is named postgres in you `inventory/host` file, 
```
cd dhis2-server-tools/deploy/inventory/host_vars/
cp postgres.template postgres
```
Example config
```
pg_max_connections: 400 

pg_shared_buffers: 8GB

pg_work_mem: 20MB

pg_maintenance_work_mem: 3GB

pg_effective_cache_size: 10GB
```

<table>
 <tr>
    <th style="text-align: left; vertical-align: top;">Parameter</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
<tr>
    <td style="vertical-align: top; text-align: left;"><code>postgresql_version</code></td>
    <td> Version for PostgreSQL to be installed, default: 13 </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>pg_max_connections</code></td>
    <td> Maximum allowed connections to the database </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>pg_shared_buffers</code></td>
    <td> Shared Buffers for postgresql,<br> recommended <code>0.25 x Available_RAM</code> for PostgreSQL </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>pg_work_mem</code></td>
    <td> PostgreSQL work memory, <br> Recommended = <code>(0.25 x Available_RAM)/max_connections</code> </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>pg_maintenance_work_mem</code></td>
    <td> As much as you can reasonably afford.  Helps with index generation during the analytics generation task <br> </td>
  </tr>
   <tr>
    <td style="vertical-align: top; text-align: left;"><code>pg_effective_cache_size</code></td>
    <td> Approx <code>80% of (Available RAM - maintenance_work_mem - max_connections*work_mem)</code> </td>
  </tr>
</table>

## lxc container management
lxd environment offers `lxc` command line tool which can be used to manage and
administer containers

<table>
  <tr>
    <th style="text-align: left; vertical-align: top;">Command</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>lxc stop container_name</code></td>
    <td>Stops a running lxd container</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>lxc restart container_name</code></td>
    <td>Maximum allowed connections to the database</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>lxc exec container_name -- command_here</code></td>
    <td>Access the Shell of a Container</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>lxc delete container_name</code></td>
    <td>Deletes and lxc container, if its stopped, use <code>--force</code> to delete running container</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>lxc file push myfile.txt my-container/root/</code></td>
    <td>Example pushing a file to the container<br></td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>lxc config show container_name</code></td>
    <td>Show Container Configuration</td>
  </tr>
</table>

##  service management with systemctl
The tool installs various applications such as tomcat9, postgresql, nginx, or
apache2, and sets up systemd services for managing them. Here are a few
examples:
<table>
  <tr>
    <th style="text-align: left; vertical-align: top;">Command</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl stop  postgresql</code></td>
    <td>Stops a postgresql Service</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl start   postgresql</code></td>
    <td>Start postgresql Service</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code> systemctl restart postgresql </code></td>
    <td>Restarts PostgreSQL service</td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl  stop tomcat9 </code></td>
    <td>Stops Tomcat9 Service </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl  start tomcat9 </code></td>
    <td>Starts Tomcat9 Service <br></td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>systemctl  restart tomcat9</code></td>
    <td>Restarts Tomcat9 Service </td>
  </tr>
</table>

## Monitoring
By default the script implements monitoring with munin and glowroot. Munin is
for server monitoring whereas glowroot is for tomcat application monitoring and profiling.  

You can access munin on https://<fqdn>/munin and glowroot is available on
https://<fqdn>/app_name-glowroot where app_name is your running dhis2
instances name. 

Ensure you secure these monitoring apps. Setting password for glowroot is
pretty straight forward. You could add new admin user with super secret
password and deleting anonymous user which is usually the default.   
