# Dhis2-database integration 

## Introduction
Before deploying dhis2 applications, follow these steps to ensure your
PostgreSQL database is set up correctly and accepting connections from the
dhis2 application:
1. Install PostgreSQL: Follow the installation guide to set up PostgreSQL on
   your system.
2. Create Database and User: After installing PostgreSQL, log in to the DBMS
   (Database Management System) and create a database, user, and password. The
   dhis2 application will connect using these parameters.
3. Configure pg_hba: In the pg_hba file (Host-Based Authentication), allow
   access from the application host network/IP address. This ensures that the
   dhis2 application can connect to the database.
4. Whitelist App IP Address: If you have a firewall running on the database
   level, make sure to whitelist the IP address of the dhis2 application for
   TCP connectivity.

To achieve these configurations, you can either run the commands manually or
use an Ansible playbook for automation. This ensures that your PostgreSQL
database is properly set up and ready to accept connections from the dhis2
application, allowing for a smooth deployment process.

## Steps

### Step1- connect to the database

`sudo -u postgres psql` 

### Step2 - Create instance database role

```
    create role  <role_name>  identified by <role_password>
```

### Step3 - Create instances database

```
    create database <database_name> owned by <role_name>;
```

### Step4 - Create create  extensions

```
    posgis 
```

### Step5 - Verify you can connect. 

```
	psql -U <role_name> -d <database_name> -W -h 127.0.0.1 -p 5432 
```

### Step6 - Allow your application on database (pg_hba.conf)  and  host firewall  

#### pg_hba.conf 

* PostgreSQL Access Control configuration, `pg_hba.conf`  has access control
  settings. These settings restrict  unwanted access to the database. It has
  five parts, 

    **TYPE, DATABASE,USER, ADDRESS **and** METHOD.**

    The "postgresql.conf" file also allows you to specify the location of the
    "pg_hba.conf" file. It is usually in
    <code>[/etc/postgresql/13/main](https://github.com/dhis2/dhis2-server-tools/blob/main/deploy/roles/postgres/files/dhispg.conf)</code>/pg_hba.conf
    by default if you install pg_version 13, for example. 

    <code>vim
    [/etc/postgresql/13/main](https://github.com/dhis2/dhis2-server-tools/blob/main/deploy/roles/postgres/files/dhispg.conf)</code>/pg_hba.conf 

    You’ll add lines below the file, they’ll look like below two entries. 

```
# TYPE   DATABASE        USER         ADDRESS                METHOD
host    <databas_name>   <role_name>  <app_server_ip>/32     md5
```

#### Host Firewall 
To secure your database server, you should assign it a private IP address and
restrict access from the internet. You can also enable the Uncomplicated
Firewall (UFW) to further protect your server. By opening only the necessary
ports, you can minimize potential vulnerabilities.

Here is a more detailed explanation of each step:

* Assigning a private IP address will prevent unauthorized users from accessing
  your database server directly from the internet. This is because private IP
  addresses are not routable on the public internet.
* Enabling UFW will block all incoming traffic by default. You can then open
  specific ports as needed, such as the port that your database server uses to
  listen for connections.
* Opening only the necessary ports will help to minimize potential
  vulnerabilities. If you open more ports than you need, you are increasing the
  attack surface of your server.

By following these steps, you can help to keep your database server secure from
unauthorized access.

Here are some additional tips for securing your database server:

* Use strong passwords for your database users.
* Encrypt your database data.
* Back up your database regularly.
* Monitor your database server for suspicious activity.

By following these tips, you can help to protect your database data from
unauthorized access and malicious attacks.

Below are examples of ufw commands allowing ssh access and db access from the
application server. 

```
sudo ufw allow proto tcp from <instnce_ip> to 0.0.0.0 port 5432 comment "dhis2 instance" 
sudo ufw allow proto tcp from 0.0.0.0 to 0.0.0.0 port 22 comment "ssh traffic"
sudo ufw enable
```

# Conclusion

After your database configuration, you should be able to connect to the
database with psql on the localhost (127.0.0.1). Check your firewall settings
and hba settings and ensure your application server is allowed to connect to
the database, i.e it ip address is white-listed on pg_hba.conf file. If it's
not, you’ll need to add a line that looks like the line below and restart your
database. 

# ansible playbook
```
- hosts: 127.0.0.1 
  become: true
  gather_facts: true
  tasks:
    # Check if dhis2.conf exists
    - name: "Create instances database role:"
      become: true
      become_user: postgres
      community.general.postgresql_user:
        name: "{{ item }}"
        state: present
        password: "{{ hostvars[item]['db_password'] }}"
      loop: "{{ groups['instances'] }}"
      when:
        - hostvars[item]['db_password'] is defined
        - inventory_hostname == hostvars[item]['database_host']
      notify: Reload Postgres
    
    # Creating instances databases
    - name: "Creating dhis2 database/databases"
      become: true
      become_user: postgres
      community.postgresql.postgresql_db:
        name: "{{ item }}"
        state: present
        owner: "{{ item }}"
      loop: "{{ groups['instances'] }}"
      when:
        - inventory_hostname == hostvars[item]['database_host']
      notify: Reload Postgres
    
    # Creating postgresql extensions
    - name: "Creating postgis,btree_gin and pg_trgm extensions"
      become: true
      become_user: postgres
      community.general.postgresql_ext:
        db: "{{ item.0 }}"
        name: "{{ item.1 }}"
      with_nested:
        - "{{ groups['instances'] }}"
        - "{{ postgresql_extensions }}"
      when:
        - hostvars[item.0]['db_password'] is defined
        - inventory_hostname == hostvars[item.0]['database_host']
      loop_control:
        label: "{{ item.1 }}"
      notify: Reload Postgres
```
