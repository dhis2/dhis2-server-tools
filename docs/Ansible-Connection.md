# ansible Connection
Ansible supports various connection plugins, you could get the list of the
supported plugins by running
```
ansible-doc --type connection -l
```
The type of Architecture you are adopting determines which connection
you'll be using. For example, if you're setting up dhis2 on an single server using
lxd containers, your connection will be 'lxd'. However, Secure Shell (SSH) is the
default connection plugin for ansible.

## lxd connection 
When the setup is all in a single server, we separate components with lxd
containers. To automate running tasks inside these containers with ansible,
there is already a connection plugin available. It's the [lxd plugin](https://docs.ansible.com/ansible/latest/collections/community/general/lxd_connection.html). 

## ssh connection
In case your servers are distributed, and you  are doing your deployment from a
central deployment server, you will be using the SSH connection plugin. 

# Conclusion
In an hybrid architecture, you'll be adopting both lxd and ssh connection by
specifying specific connection variable per host with a variable
`ansible_connection`

Read More on [Ansible Connection Plugins](https://docs.ansible.com/ansible/latest/plugins/connection.html)
