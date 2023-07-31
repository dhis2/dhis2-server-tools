# instance monitoring with munin
Everything documented here is automated with ansible and this is just for user understanding. 
munin is a  software monitoring tool that can be used to monitor instances, which can either be containers, physical severs or virtual servers, (at least in our case ). 
this document will guide on the installation and configuration of the munin (server) and munin-node (client/monitored-hosts). 

This monitoring tool will be installed with ansible scripts, below tasks are automated. 

## munin sever 
install munin monitoring software package , i.e apache2 libcgi-fast-perl libapache2-mod-fcgid
 * server update `apt update`
 * software install `apt install apache2 libcgi-fast-perl libapache2-mod-fcgid`
 * munin install `apt install munin` this command will install munin, munin-node, and munin plugins extra

#### enabling plugins
enabling munin plugins for postgresql monitoring 

#### editing munin configuration file 
after munin is installed, also a configuration file will be included in `/etc/munin/munin.conf`, this file will be edited with ansible and below lines will be an-commented. 

```
dbdir /var/lib/munin
htmldir /var/cache/munin/www
logdir /var/log/munin
rundir /var/run/munin
```

#### configure apache for munin server monitoring
ansible will also enable apache web server for munin monitoring by creating a symlink to `/etc/apache2/conf-enabled/munin.conf`
`ln -s /etc/munin/apache24.conf /etc/apache2/conf-enabled/munin.conf`

#### configure munin for external access, 
ansible will be edited `/etc/munin/apache24.conf`, replacing a line `require local` with `require all granted`  and changing `options` value from `none` to `followsymlinks symlinksifownermatch `

#### reloading services 
after the installation is complete, services will be reloaded. These services includes:-
* apache2
* munin 
* munin-node

## munin node (monitored nodes)
after setting up munin server, ansible will also configure hosts that will eventually be monitored. 
to monitor instances, install munin-node on those instances, `apt install munin-node` 
#### editing configuration file on the agents
ansible will be editing a file (located on `/etc/munin/munin-node.conf`) on the monitored hosts.
i will add a line that will white list munin server's ip address, looks like `allow ^192\.168\.0\.108$`
however, in our case we've installed cidr perl module and our line would look like `cidr_allow 192.168.0.30/32`

#### restart munin node service
after editing munin node file, restart the service, in our case automated with ansible. 
`sudo service munin-node restart`


## communication between munin server and the nodes.
Ansible will finally edit configuration file on the server, i.e `/etc/munin/munin.conf` file adding monitored nodes addresses. 
sample configuration shown below. 
```
[node0.example.com]
       address 192.168.0.106
         use_node_name yes
```
