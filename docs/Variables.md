# Server Tools Variables { #dhis2_server_tools_variables }
Ansible uses variables to handle system differences. In dhis2-server-tools,
specific variables are defined PostgreSQL, dhis2 instance, proxy, and monitoring systems. While you
can define variables in various places like playbooks, roles, or host files, we
mainly define them in the `dhis2-server-tools/deploy/inventory/hosts` file,
created from `hosts.template.` Customize these variables to fit your environment.

In inventory hosts file, hosts are grouped in [group_names], in our case we
have `[databases],` `[instances],` `[web]` and `[monitor]` groups .Variables not assigned
to any specific group belong to the `[all]` group. To tie
variables to a particular group, place them under `[group_name:vars]`, e.g ,
`[instances:vars]`. If you want a variable to apply to a specific host, append
it to the host line. For example, to add `database_host` and `dhis2_version` to
the dhis host in the `instances` group, use the following format:

```
[instances]
dhis  ansible_host=172.19.2.11  database_host=postgres  dhis2_version=2.39 
```
 Another option is to create a file in the `inventory/host_vars/` directory
 with the same name as the host in your `inventory/hosts` file. The benefit of
 this approach is that you can encrypt the file using `ansible-vault` for added
 security. Any variables you define in the `host_vars` directory will take
 precedence over those in `inventory/hosts` file 

```
touch inventory/host_vars/dhis
vim inventory/host_vars/dhis
```
Add the variables using `yaml` syntax as its shown below 

```
ansible_host: 172.19.2.11
database_host: postgres
dhis2_version: 2.39
```

## Here's the list of available configuration parameters and their default values
### General Variables { #dhis2_server_tools_general_variables } 
---
<table>
  <tr>
    <th style="text-align: left; vertical-align: top;">Variable</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>timezone</code></td>
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
<tr>
     <td style="vertical-align: top; text-align: left;"><code>lxd_network</code></td>
    <td>Here you define a network which your containers will be created into,
    default is <code>172.19.2.1/24</code> </td>
  </tr>
 <tr>
<tr>
     <td style="vertical-align: top; text-align: left;"><code>lxd_bridge_interface</code></td>
    <td>The name of the created lxd bridge, default is <code>lxdbr1</code> </td>
  </tr>
 <tr>
</table>

### Instance Variables { #dhis2_server_tools_instance_variables }
<table>
 <tr>
    <th style="text-align: left; vertical-align: top;">Variable</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"> <code>fqdn</code></td>
    <td> This is the domain used to access dhis2 application <br>Strictly required for Letsencrypt to work </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>create_db</code></td>
    <td> Whether the database should be created or not <br>Choices:</strong>
    <br> <ul><li>True  ← (default) </li><li>False</li></ul> </td>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>database_host</code></td>
    <td> Host to use as your database server <br> Default=<code>postgres</code> </td>
  </tr>
<tr>
    <td style="vertical-align: top; text-align: left;"><code>dhis2_war_file</code></td>
    <td> Source for your dhis2 war file, can either be remote or available
    locally  as file  <br>Examples</strong> <br>
    <ul><li><code>"https://releases.dhis2.org/2.38/dhis2-stable-2.38.0.war"</code>
    </li><li><code>/full/path/for/your/dhis2.war</code></li></ul> </td>
  </tr>
<tr>
    <td style="vertical-align: top; text-align: left;"><code>dhis2_version</code></td>
    <td> You can specify just the major version of dhis2 and it will get its
    latest stable iteration from  <a href="
    https://releases.dhis2.org">https://releases.dhis2.org</a>. <br>If your
    have both <code>dhis2_war_file</code> and <code>dhis2_version</code>
    defined, <code>dhis2_war_file</code> wins,
    <br>Examples</strong> <br> <ul><li><code>2.39</code>
    </li><li><code>2.38</code></li></ul> </td>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>heap_memory_size</code></td>
    <td> This is tomcat  Java Heap Memory Size,   <br>Example</strong> <br>
    <code>heap_memory_size=2G </code> </td>
  </tr> </tr>
</table>

### PostgreSQL Variables { #dhis2_server_tools_postgresql_variables }

| Variable                     | Comments |
|:-----------------------------|:---------|
| `postgresql_version`         | PostgreSQL version to install. Default is `16` for fresh installs. |
| `pg_max_connections`         | Maximum allowed database connections. |
| `pg_shared_buffers`          | Shared buffers for PostgreSQL. Recommended: `0.25 x Available_RAM`. |
| `pg_work_mem`                | Work memory per query. Recommended: `(0.25 x Available_RAM) / max_connections`. |
| `pg_maintenance_work_mem`    | Memory for maintenance tasks like index creation. Allocate as much as reasonably possible. |
| `pg_effective_cache_size`    | Approx. `80% of (Available_RAM - maintenance_work_mem - max_connections * work_mem)`. |

### Proxy Variables { #dhis2_server_tools_proxy_variables}
<table>
 <tr>
    <th style="text-align: left; vertical-align: top;">Variable</th>
    <th style="text-align: left; vertical-align: top;">Comments</th>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>email</code></td>
    <td>Strictly required if you are using Letsencrypt</td>
  </tr>
<tr>
    <td style="vertical-align: top; text-align: left;"><code>proxy</code></td>
    <td> Proxy software of your choice <br> <strong>Options</strong> <br>
    <ul><li>nginx  ← (default)</li><li>apache2</li></ul> </td>
  </tr>
 <tr>
    <td style="vertical-align: top; text-align: left;"><code>SSL_TYPE</code></td>
    <td> This parameter enables to specify whether you'd want to use
    <code>letsencrypt</code> or your own <code>customssl</code>
    certificate,<br> <strong>Options</strong> <br> <ul><li>letsencrypt ←
    (default)</li><li>customssl</li></ul> </td>
  </tr>
  <tr>
    <td style="vertical-align: top; text-align: left;"><code>munin_base_path</code></td>
    <td> Base path for accessing munin, e.g:
    https://domain.example.com/munin_base_path  defaults to <code>munin</code>
    </td>
</tr>
<tr>
    <td style="vertical-align: top; text-align: left;"><code>munin_users</code></td>
    <td>A list of users with their corresponding passwords allowed to login to munin: 
    Example: 
   <pre>
   <code>
munin_users:
  - name: admin
    password: admin_password
  - name: user2
    password: user2_passsword
  </code>
  </pre>
  Default username and password is admin and district respectively. 
 </tr>
</table>

| Variable          | Comments |
|:------------------|:---------|
| `email`           | Strictly required if you are using Let's Encrypt. |
| `proxy`           | Proxy software of your choice.<br>**Options**:<br>- nginx ← (default)<br>- apache2 |
| `SSL_TYPE`        | Choose whether to use `letsencrypt` or a `customssl` certificate.<br>**Options**:<br>- letsencrypt ← (default)<br>- customssl |
| `munin_base_path` | Base path for accessing Munin, e.g., `https://domain.example.com/munin_base_path`. Defaults to `munin`. |
| `munin_users`     | A list of users and passwords allowed to log into Munin. See example below. |

**Example:**
```yaml
munin_users:
  - name: admin
    password: admin_password
  - name: user2
    password: user2_passsword
```

### backup related Variables
These variables pertain to the PostgreSQL database host and contain sensitive
information. It is advisable to secure them using ansible-vault encryption. You
have the flexibility to define these variables in different locations, but it
is recommended to place them in the host file within the host_vars directory,
as shown below:

`dhis2-server-tools/deploy/inventory/host_vars/postgres`

| Variable         |Comments |
|:------------------|:----------|
| `s3_access_key`  | This is a unique identifier for a cloud user or programmatic entity (like an application) that needs to interact with object storage. |
| `s3_secret_key`  | This is a secret piece of information associated with the access key. It is used to digitally sign requests made to object storage and possibly other services. This key must be kept confidential, as it authenticates and authorizes requests on behalf of the access key. |
| `s3_cluster_id`  | Cluster URL for Object Storage is unique to each data center. Different data centers have unique cluster IDs. Refer to [Linode Object Storage Guide](https://www.linode.com/docs/products/storage/object-storage/guides/urls/#cluster-url-s3-endpoint) for Linode. |
| `s3_bucket`      | This is a container or storage resource for storing files in the context of object storage. |

</table>
