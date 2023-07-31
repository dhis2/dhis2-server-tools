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
