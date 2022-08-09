# Monitoring 
Monitoring is broadly clasified into application and server. There are tools
that offers both application and server monitoring, while others dont.
Monitoring is implemented with ansible playbook on a relative path
`../deploy/roles/monitoring/tasks/main.yml` Note that is is the main playbook
and it only call Monitoring implemetation specific to a user. With this tools,
we've implemented two monitoring solutions with open source tools, namely munin
and zabbix.

DHIS2 monitoring is divided into two
1. server/intance monitoring 
2. application monitoring Application is monitored with glow-root and the
   server is monitored with either zabbix or munin open source tools. There is
   a switch/option to choose the type that you'd want for your enviromnet. 

## Zabbix Zabbix monitoring will be setup only if your server monitoring tool
of choice is zabbix.  Threre is a asible role named monitor, It doed the
following 
* Install zabbix server on the monitoring server 
* configur zabbix server
* install agents on the hosts 
* open firewall on th hosts, port 10050
* open firewall on the agennts, monitored hosts. 

## Munin setup Asible will be seting up muning on the monitoring and the
monitored hosts, ### Monitoring server 
* install monitoring server 
* deploy configuration 

### Monitored hosts
* install the munin-node i.e monitoring agent 
* deploy configuration on the moniring node and add alsot to the moniroting
  server  
* open the host firewall from the monitoring server to the default munin-node
  port 4949
* restart munin node 

ifconfig 
/Users/ktito/dhis2-server-tools/docs
