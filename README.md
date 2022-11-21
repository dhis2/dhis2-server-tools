# dhis2-server-tools

This tools install DHIS2 application stack with ansible. The stack is comprised
of dhis2 tomcat instance(s), database(postgresql), proxy (nginx/apache2) and
monitoring (munin).
Ths installation can be single server or on multiple servers. Single server setup is using lxd. 

1. setup on a single ubuntu server<br> 
    Uses lxd containers, set `ansible_connection` to `lxd`.
2. Setup on multiple servers.<br> 
    dhis2 application stack, i.e database, apps,monitor and proxy are setup on
    on separate virtual machines or servers. 

## Pre-requisites
Before you start installation, you will need -:,
* fqdn (fully qualified domain name). <br>
  It should be mapped to server or proxy public ip address depending on your setup. <br> 
* ubuntu server running 20.04 or 22.04. 
* SSL/TLS certificate - The installation defaults to obtaining SSL/TLS
  certificate from letsencrypt, you can also bring your own.  
* good internet on the severs.
## Installation
The process of installation involves pulling deployment code from git and
setting a few variables/parameters to suit your environment. Of the importance
is `fqdn`,`email` and `ansible_connection,` other config parameters can be left in their defaults.  
1. single server
    * ansible_connection should be set to *lxd* 
    * dhis2 and its components will be installed on *lxd* containers. 
    * deployment happens from within the server, you do not need separate deployment server. 

2. multiple servers environment setup. 
    * `ansible_connection` should be set to `ssh`
    *  A separate deployment server is a requirement, it should be able to
       access all the other servers via ssh 

### Step1 :- Install ansible and other dependencies.
#### environment setup. 
_**NOTE:** In case of multiple server setup, this happens on the deployment server._ <br> 
update and upgrade system packages <br>
```
sudo apt -y update
sudo apt -y upgrade
```
Ensure git is installed. <br>
`sudo apt install -y git`

Install ansible version **_2.11_** or above, to work with community.general modules.

```
sudo apt install -y  software-properties-common
sudo apt-add-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible
sudo apt-get install -y python3-netaddr
```
Install community.general ansible modules, required for lxd_container, ufw and other modules <br>
`ansible-galaxy collection install community.general -f`

### Step2 :- Pull ansible deployment code from git
`git clone https://github.com/dhis2/dhis2-server-tools`

### Step3:- Customization before installation
Change the directory to the project directory
```
cd dhis2-server-tools/deploy
```
edit the file  `./inventory/hosts`. The file has a list
of hosts, which can be physical, virtual servers or lxd containers depending on
your setup architecture and configuration parameters. 
#### hosts configuration 
Change ip address for these hosts to suite network environment. <br>
_**NOTE**: `When the install is on a single host with lxd, ensure your
lxd_network is unique and  not overlaping with any of your already existing
host network.`_ <br> 

Use an editor of your choice, here we are using vim, you could use `nano` as well. <br> 
`vim ./inventory/hosts`

##### Sample host configuration 
```
[proxy]
proxy       ansible_host=192.168.0.2 
[databases]
postgres    ansible_host=192.168.0.20
[instances]
hmis  ansible_host=192.168.0.10  database_host=postgres  
[monitoring]
```
####  Configuration parameters 
dhis2-server-tools configurations are located on the same inventory file , i.e 
`dhis2-server-tools/deploy/inventory/hosts`.

Below is a list of available configuration parameters, of importance is fqdn and email, ( mail required for letsencrypt cert expiry notification )
##### important configuration parameters 
Your proxy setup will need these two variables be set for it to work. 
* `fqdn` this is the domain used to access dhis2 application 
* `email` This is an email used to generate letsencrypt certificate and letsencrypt expiration emails
* `ansible_connection` parameter is also a requirement, it defaults to `lxd`, however is you are setting up dhis2 over ssh, on multiple servers you'll need to change it to `ssh`

_Important: dhis2 is designed to work on the dedicated domain. You can use
either a domain like yourdomain.com or a subdomain of any level. During the
installation, the install checks the existence of the domain name entered
(otherwise proxy setup is aborted). Therefore, you need to create and setup a
(sub)domain so it is resolved to an external IP address of your server._

##### optional parameters 
* `proxy=nginx`  here you specify proxy software of your choice, can be nginx
  or apache2 default is nginx, only nginx supported for now. 
* `SSL_TYPE=letsencrypt` this parameter enables to specify whether you'd want
  to use `letsencrypt` or your own `customssl` certificate, defaults is
  letsencrypt 
* `timezone=Africa/Nairobi` You set this variable to your home/city's time zone. 

* `lxd_network="192.168.0.1/24"`, here you define a network which your
  containers will be created into.
* `lxd_bridge_interface=lxdbr0`, the name of the created lxd bridge
* `create_db=yes` , whether dhis2 install should create new db or not, 
* `JAVA_VERSION="11"` version of java to be install, defaults to java11
* `dhis2_war_file` This is were you specify dhis2 war file, its can be a
  url or a file,the file full path must be specified, alternatively, you can
  place the file in
  dhis2-server-tools/deploy/dhis2/files directory and you'll not be required to
  specify its path but just the name. 
* `database_host=postgres` this is the database server that the instance should
  use, defaults to postgres. Must be also defined on you inventory file. 

#### hosts grouping
The host are grouped into categories below, 
* `[proxy]` - These are the servers that are used to access dhis2 application
  from the outside. Public ip address is mapped to this host. In most cases
  it’s just a single host but you can have multiple servers as well.
* `[database]` - This is a group of servers that are used to host the databases,
  which is postgresql in our case. It can be one or many as well.
* `[instances]` - Servers intended for installing dhis2 web  application will be
  under this group.
* `[monitoring]`  - Servers intended for monitoring.


### Step4: The installation
#### DHIS2 setup on a single host with lxd 
To install dhis2 on a single server (lxd), ensure your ansible_connection
parameter is set to `lxd` <br>
`ansible_connection=lxd` <br>
Navigate to the deploy directory, `cd dhis2-server-tools/deploy/` <br>
Run below two playbooks on the host where you'll be setting up dhis2, remember,
ensure you are on `deploy` directory for the scripts to work.

`sudo ansible-playbook lxd_setup.yml`    # this sets up lxd environment., -K is
for privilege escalation <br>
`sudo ansible-playbook dhis2.yml` # this deploys the app on lxd containers <br>

#### DHIS2 install on multiple servers
You'll need a deployment server for this architecture, it is from the
deployment server that you'll be running your ansible scripts. It needs to have
ssh connection to the other hosts.  Ensure ansible_connection parameter is set
to ssh, i.e` ansible_connection=ssh` then run the playbook below, and ip
addresses of the hosts are correctly configured on the inventory file.  You'll
run your script, again from within deploy directory, navigate into it with `cd`
command. <br> and run below ansible command to begin your installation. 

`ansible-playbook dhis2.yml -u <ssh_user> -Kk`

NOTE: Since connection used is ssh, you'll need to pass connection parameters
on the command line, i.e ssh_user with `-u`, ssh_password with `-k` and
become_password  with `-K`. For this to work, ssh connection from the
deployment server should be working, perhaps you'll need to test the connection
before the installation. 

## Using a Custom SSL Certificate 
##### ENSURE YOU HAVE SSL/TLS Certificate and key beforehand
For HTTPS connection, the install used Letsencrypt to obtain an SSL/TLS certificate. This
should work fine most OS and browsers, however, these scripts provides a way of
using your own SSL/TLS certificates. To use your own custom SSL/TLS certs, follow below steps, 

1. Get/generate `fullchain.pem` file which will be concatenating your certificate
   and any other intermediate and root certificates.
2. Get/generate `privkey.pem` file, this contains private key used for certificate signing.
3. Copy these two files into `dhis2-server-tools/deploy/roles/proxy/files/` directory.
4. edit `dhis2-server-tools/deploy/inventory/hosts` and change `SSL_TYPE`  to `customssl` 

To start using a custom certificate instead of the default Letsencrypt
certificate, you need to switch off the certbot service in the `/deploy/inventory/hosts` 
configuration and ensure you have both `fullchain.pem` and `private.pem` files

## Customizing postgresql
Installed postgresql database comes with default settings which should be fine
and working at this stage. However, these settings can be changed a bit for
performance optimization and maximum utilization of the available system
resources. Before optimizing anything, you will need to know resources you have
first, i.e, total RAM  available, use `free -h` for that.

#### limiting  RAM exposed to postgresql container, only applies for lxd setup
Deciding how much RAM to dedicate to postgresql depends a little on how many
DHIS2 instances you are likely to run, but assuming you will have a production
instance and perhaps a small test instance,if you gave a total of say 32GB,
giving 16GB exclusively to postgresql is a reasonable start.

`sudo lxc config set postgresql limits.memory 16GB`

running `free -gh` inside the postgresql container you will see that it no
longer can see the full amount of RAM, but has been confined to 16GB. (try sudo
lxc exec postgres -- free -gh).

#### Editing postgresql configuration, applies for both both lxd and ssh setup.

Depending on your setup, postgresql can be on either the containers or on its own server,
To access the container  `sudo lxc exec postgres bash`

Access postgresql server from the deployment server with `ssh ssh_user@postgresql_server_ip -p ssh_port`

The file where all your custom settings are made is called `/etc/postgresql/13/main/postgresql.conf`
The default contents of this file is shown below:

```
# Postgresql settings for DHIS2

# Adjust depending on number of DHIS2 instances and their pool size
# By default each instance requires up to 80 connections
# This might be different if you have set pool in dhis.conf
max_connections = 200

# Tune these according to your environment
# About 25% available RAM for postgres
# shared_buffers = 3GB

# Multiply by max_connections to know potentially how much RAM is required
# work_mem=20MB

# As much as you can reasonably afford.  Helps with index generation
# during the analytics generation task
# maintenance_work_mem=512MB

# Approx 80% of (Available RAM - maintenance_work_mem - max_connections*work_mem)
# effective_cache_size=8GB

# This setting is suitable for good SSD disk.  For slower spinning disk consider
# changing to 4
random_page_cost = 1.1

checkpoint_completion_target = 0.8
synchronous_commit = off
log_min_duration_statement = 300s
max_locks_per_transaction = 1024
```

The 4 settings that you should uncomment and give values to are
`shared_buffers, work_mem, maintenance_work_mem` and `effective_cache_size`.
If your database have say, 16GB of RAM reserved, It will be reasonable having
below settings
```
shared_buffers = 4GB
work_mem=20MB
maintenance_work_mem=1GB
effective_cache_size=11GB
```
For these changes to take effect, to restart the database and the dhis2 in that
order, for lxd setup, just restarting the containers restarts the apps. 
#### lxd setup restart example 
```
sudo lxc stop <dhis2_container>
sudo lxc restart postgres
sudo lxc start covid19
```

#### application management on the distributed architecture. 
for dhis2 setup in a distributed architecture, you'll have to logging to the
individual server and restart respective application. 
to restart postgres database, login to the server via ssh and run the command
below, 

   ```
   systemctl  stop  postgresql
   systemctl  start   postgresql
   systemctl  restart postgresql # this restarts the database with a sigle command 
   ```
To restart dhis2 instance, login to the server and use systemctl to restart
tomcat service by either stopping and starting or restarting with a single
command. 
   ```
   systemctl  stop tomcat9 
   systemctl  start tomcat9 
   ```
You can restart with below single command<br>
 `systemctl  restart tomcat9` 
   

Postgresql is an extremely customizable  database with multiple configuration
parameters. This brief installation guide only touches on the most important
tunables.

## lxd container operation
lxd environment offers `lxc` command line tool which can be used to manage and
administer containers 

listing containers <br>
`lxc list`
```
+----------+---------+---------------------+------+-----------+-----------+
|   NAME   |  STATE  |        IPV4         | IPV6 |   TYPE    | SNAPSHOTS |
+----------+---------+---------------------+------+-----------+-----------+
| dhis2    | RUNNING | 192.168.0.10 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| monitor  | RUNNING | 192.168.0.30 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| postgres | RUNNING | 192.168.0.20 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| proxy    | RUNNING | 192.168.0.2 (eth0)  |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| training | RUNNING | 192.168.0.12 (eth0) |      | CONTAINER | 0         |
p----------+---------+---------------------+------+-----------+-----------+
```
stop a container <br>
`lxc stop <container_name>`

restart container <br> 
`lxc restart <container_name>`

deletes a container<br>
`lxc delete <container_name>`
## MONITORING
By default the script implements monitoring with munin and glowroot. Munin is
for server monitoring whereas glowroot is for tomcat application monitoring.  

