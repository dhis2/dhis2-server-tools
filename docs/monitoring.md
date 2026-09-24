# Monitoring 
Monitoring is broadly classified into application and server. There are tools
that offers both application and server monitoring, while others don't.
Monitoring is implemented with ansible playbook on a relative path
`../deploy/roles/monitoring/tasks/main.yml` Note that is is the main playbook
and it only call Monitoring implementation specific to a user. With this tools,
we've implemented two monitoring solutions with open source tools, namely munin
and zabbix.

DHIS2 monitoring is divided into two
1. server/instance monitoring 
2. application monitoring Application is monitored with glow-root and the
   server is monitored with either zabbix or munin open source tools. There is
   a switch/option to choose the type that you'd want for your environment. 

## Zabbix Zabbix monitoring will be setup only if your server monitoring tool
of choice is zabbix.  There is a ansible role named monitor, It does the
following 
* Install zabbix server on the monitoring server 
* configure zabbix server
* install agents on the hosts 
* open firewall on the hosts, port 10050
* open firewall on the agents, monitored hosts. 

## Munin setup ansible will be setting up munin on the monitoring and the
monitored hosts, ### Monitoring server 
* install monitoring server 
* deploy configuration 

### Monitored hosts
* install the munin-node i.e monitoring agent 
* deploy configuration on the monitoring node and add also to the monitoring
  server  
* open the host firewall from the monitoring server to the default munin-node
  port 4949
* restart munin node 

## Grafana, Prometheus and Loki
Set `server_monitoring` to `grafana`, `prometheus` or `grafana/prometheus`
(they are equivalent) to install this stack on the monitoring host:
* Prometheus, scraping `postgres_exporter` on the database hosts, the DHIS2
  `/api/metrics` endpoint of each instance, node exporters and Loki itself
* Grafana, with Prometheus and Loki datasources and the bundled dashboards,
  served through the proxy under `/grafana` (or directly over the VPN when
  WireGuard monitoring lockdown is on)
* Loki (disable with `loki_enabled=false`), storing logs under
  `/var/lib/loki` with `loki_retention_period` retention (default 30 days).
  Port 3100 is opened only to the proxy hosts, for log shippers to push to;
  Loki is not published through the proxy and is queried through Grafana.

