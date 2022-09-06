## Customizing postgresql
Installed posgresql database comes with default settings which should be fine and working at this stage. However, these settings can be changed a bit for perfonance optimization and maximux utilization of the availlable system resources. Before optimizing anything, you will need to know reources you have first, i.e, total RAM  availlable, use `free -h` for that. 
### CASE I: Setup with lxd on sigle server.
Deciding how much RAM to deidicate to postgresql depends a little on how many DHIS2 instances you are likely to run, but assuming you will have a production instance and perhaps a small test instance,if you gave a total of say 32GB,  giving 16GB exclusively to postgresql is a reasonable start. 

`sudo lxc config set postgresql limits.memory 16GB`


running `free -gh` inside the postgresql container you will see that it no longer can see the full amount of RAM, but has been confined to 16GB. (try sudo lxc exec postgres -- free -gh).

### CASE II: Editing postgresql configuration, applies for both both lxd and ssh setup.  

Depeniding on your setup, postgresql can be on either the containers or on its own server, 
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

The 4 settings that you should uncomment and give values to are `shared_buffers, work_mem, maintenance_work_mem` and `effective_cache_size`.  If your database have say, 16GB of RAM researved, It will be resonable haveing begqqquuulow settings 
```
shared_buffers = 4GB
work_mem=20MB
maintenance_work_mem=1GB
effective_cache_size=11GB
```
Before applying these settings you should shutdown any running DHIS2 instances. So, for example, back on the host:

sudo lxc stop covid19
sudo lxc restart postgresql
sudo lxc start covid19
Postgresql is an extremely configurable database with hundreds of configuration parameters. This brief installation guide only touches on the most important tunables.

(TODO: install postgresql munin plugin)




