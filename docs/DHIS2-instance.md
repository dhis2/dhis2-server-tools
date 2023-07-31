# DHIS2 instance 

## Introduction

DHIS2, a web application built on Java, operates on the Apache Tomcat web
server and relies on PostgreSQL as its backend database for persistent data
storage. In this tutorial, we will provide a comprehensive, step-by-step
installation guide for setting up DHIS2 on an Ubuntu 20.04/22.04 server and
integrating it with a PostgreSQL database. Please note that it is assumed you
have already completed the installation and configuration of PostgreSQL, which
is outlined in the [Postgresql Install Guide
](https://docs.google.com/document/d/1Lt0SplGJzJaF-rKLhDgQrTkDVbmxYA1ea8sEEJATUGg/edit).
Additionally, we will briefly discuss optimization and configuration aspects to
enhance the performance of the application.

To proceed with the following steps, you will need:

* An Ubuntu server running either version 20.04 or 22.04.
* A non-root user account with sudo privileges.
* A functioning PostgreSQL database server.
* Reliable and stable internet access.

## System software prerequisites
* apache-tomcat9
* Java JDK. OpenJDK is recommended.
    * DHIS2 version 2.38 and later, JDK 11 is required.
    * DHIS 2 version 2.35 and later, JDK 11 is recommended and JDK 8 or later is required.
    * DHIS 2 versions older than 2.35, JDK 8 is required.

## The installation. 

### Step1: Database 

Dhis2 application connects and stores its data on postgresql database. Before
deploying the app, ensure you have a running postgresql server  with dhis2
database schema and user with the password.

Below are documentation for each

Postgresql Installation 

postgresql configuration 

dhis2-database integration 

### Step2 - Create an LXD container, skip it if you are not using containers. 

When setting dhis2 on a single server, we prefer packages on our stack on lxc
containers. However, if you have dedicated instances/servers or vm running your
application, you will skip this step. 

### Step3 - Installing java  tomcat9 

Download and install required packages with Ubuntu apt package manager. JAVA
version you are installing depends on the version of dhis2 you’ll be setting up
on your system, generally, for versions 2.35 and below you use java8 and java11
otherwise. 

* Download and install the packages

```
sudo apt update 
sudo apt upgrade 
sudo apt install openjdk-11-jre-headless tomcat9 tomcat9-admin ufw unzip 
```

Step4 - Apache tomcat configuration file. 

Apache Tomcat, hosting dhis2 can be customized and configured to meet better
security and performance requirements be editing and xml config file. 

By default, the file is
<code>[/etc/tomcat9/server.xml](https://github.com/dhis2/dhis2-server-tools/blob/main/deploy/roles/dhis2/files/server.xml)</code>,
we have a sample configuration file for this. 

* Edit and populate the file with our optimized sample configuration

    ```
    sudo vim /etc/tomcat9/server.xml 

    ```

### Step5 - dhis2 configuration

DHIS2 like any tomcat application has a configuration file, within this file,
you’ll configure database connection and other parameters. 

* The default configuration file  is `/opt/dhis2/dhis.conf` you’ll be required
  to create if it's not present with two steps 

```
sudo mkdir /opt/dhis2
sudo touch /opt/dhis2/dhis.conf 
```

* Next is adding contents to the created configuration file, here is a sample
  configuration file for dhis.conf. 
  Edit the file with your favorite command line editor, you can either use vim
  or nano, in this tutorial we are going to use vim. 

    ```
    sudo vim  /opt/dhis2/dhis.conf 
    ```

What's really important for the working dhis2 instance is database connection
settings, below are the required settings, replace for your real `database_ip,
instance_database, database_role and database_role_password `as highlighted in
below excerpt. 

```
# Hibernate SQL dialect
connection.dialect = org.hibernate.dialect.PostgreSQLDialect

# JDBC driver class
connection.driver_class = org.postgresql.Driver

# Database connection URL
connection.url = jdbc:postgresql://<database_ip>/<instance_database>

# Database username
connection.username = <database_role>

# Database password (sensitive)
connection.password = <database_role_password>

# Database schema behavior, can be 'validate', 'update', 'create', 'create-drop'
connection.schema = update
```

### Step5: Download and deploy war file. 
* Download war file from [DHIS2 release page](https://releases.dhis2.org) you
  can use `wget` utility if your server is headless which is the case in most
  deployments. 

    ```
    wget https://releases.dhis2.org/40/dhis2-stable-40.0.0.war
    ```
* Extract the war file to webapps directory. With custom configuration file,
  webapp auto deployment is disabled, good for security. You however going to
  extract war file into webapps directory manually using unzip utility. 

    unzip 
	
* Restart tomcat9 

```
sudo systemctl restart tomcat9 
```

### Step6: troubleshooting

Common problems that arise are usually related to database connection, please
ensure you can connect to postgresql server form the application server, some
of the troubleshooting tip wit linux utilities, 

* Check if you can connect to the database, either use telnet or curl,
  whichever is available on your app server, commands are jotted in bold, 

    ```
    telnet <dataase_ip> <database_port>
    trying <database_ip>...
    Connected to <database_ip>
    Escape character is '^]'.

    curl -k -vvv telnet://<database_ip>:<database_port>
    * Trying <database_ip>:5432...
    * Connected to <dabase_ip> (database_ip) port 5432 (#0)

    ```

* if you see `connected`, then firewall is accepting db tcp requests from your
  app server 
* You could restart your app and follow  the logs with the below command

```
systemctl restart tomcat9; journalctl -fu tomcat9 
```

## Conclusion

If you have a properly configured and working database connection, dhis2 will
attempt to connect once you complete its installation and configuration. As
pointed out above, you might have errors and usually they are relating to the
database connection. In some other cases, they are relating to issues that
arise with the upgrades. If you are upgrading your system, it is recommended
you do a backup of your database prior. Flyway script usually does changes to
the database during the upgrade process and is usually a night mare reverting
back these changes. 

## ansible playbook
```
- hosts: 127.0.0.1 
  become: true
  gather_facts: true
  vars:
    java_version: 11
    dhis2_url: 
  tasks:
```

