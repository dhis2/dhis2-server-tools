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


