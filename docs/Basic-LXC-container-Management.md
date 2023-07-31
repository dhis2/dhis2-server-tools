# Basic LXC container management
listing containers <br>
```
lxc list

+----------+---------+---------------------+------+-----------+-----------+
|   NAME   |  STATE  |        IPV4         | IPV6 |   TYPE    | SNAPSHOTS |
+----------+---------+---------------------+------+-----------+-----------+
| dhis2    | RUNNING | 172.19.2.10 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| monitor  | RUNNING | 172.19.2.30 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| postgres | RUNNING | 172.19.2.20 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| proxy    | RUNNING | 172.19.2.2 (eth0)  |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
| training | RUNNING | 172.19.2.12 (eth0) |      | CONTAINER | 0         |
+----------+---------+---------------------+------+-----------+-----------+
```
Stop a running container 

`lxc stop <container_name>`

Restart container

`lxc restart <container_name>`

Delete a container

`lxc delete <container_name>`

Execute and run commands inside a container 

`lxc exec <container-name> -- command_here`

Access the Shell of a Container:
```
lxc exec <container_name> -- /bin/bash
```
Show Container Configuration:
```
lxc config show <container_name>
```
View Container Log:
```
lxc info my-container
```
Example (pushing a file to the container):
```
lxc file push myfile.txt my-container/root/
```
Copy Files Between Host and Container:
```
lxc file push <local_file> <container_name>/<path_inside_container>
lxc file pull <container_name>/<path_inside_container> <local_destination>
```

