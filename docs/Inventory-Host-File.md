# inventory/hosts file
Ansible operates on one or more servers, defined in an inventory file. This
file can also contain variables in `key=value` format. Inventory files can be
written in various formats, such as .INI, YAML, or JSON. In our case, we use
the INI format for its human readability.

To avoid pushing custom user configurations to the remote GitHub repository,
hosts file is excluded, we only include a template file named `hosts.template`.
This template serves as a starting point for users.

Create hosts file from the `hosts.template` to `hosts`. 

`cp dhis2-server-tools/deploy/inventory/hosts.template dhis2-server-tools/deploy/inventory/hosts`

Once the hosts file has been created, you can proceed changing variables and
customizing the host addresses to suit your network setup. Replace the
placeholders in the hosts file with the actual IP addresses or hostnames of the
servers you want to manage using Ansible. Make sure to configure the hosts and
groups according to your specific environment requirements The hosts file
contains a list of hosts grouped based on their installed components, along
with optional variables.

_**NOTE**: `When the install is on a single host with lxd, ensure your
lxd_network is unique and not overlapping with any of your host network.`_ 

## Hosts grouping
The host are grouped into categories below, 

* `[proxy]`
Put proxy hosts on this category. 
The proxy server serves as the entry point to the dhis2
application from outside the network. It has a public IP address mapped to it,
enable external access. Usually, there is only one server fulfilling this
role, and it acts as a proxy by forwarding requests to the backend servers.
Additionally, the proxy server can also function as a load balancer,
distributing incoming requests among multiple backend servers for improved
performance and scalability.

* `[database]`
This is a group of servers/containers that are used to host the PostgreSQL
database. It can be one or more. 
* `[instances]`
Servers intended for installing dhis2 web application will be under this group.
* `[monitoring]`
Servers intended for monitoring your infrastructure. 

## sample host list
```
[proxy]
proxy  ansible_host=172.19.2.2

[databases]
postgres  ansible_host=172.19.2.20

[instances]
hmis  ansible_host=172.19.2.11  database_host=postgres  dhis2_version=2.38 
dhis  ansible_host=172.19.2.12  database_host=postgres  dhis2_version=2.39 

[monitoring]
munin   ansible_host=172.19.2.30 
```
Read more on [Ansible Inventory](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html#intro-inventory)

