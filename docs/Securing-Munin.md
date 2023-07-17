# Munin Authentication 

When setting up a web server, there are often sections of the site that you
wish to restrict access to. Web applications often provide their own
authentication and authorization methods, but the web server itself can be used
to restrict access if these are inadequate or unavailable. In this guide,
you’ll password protect assets on an Nginx web server running on Ubuntu 22.04
We have a monitoring tool deploying and configured, monitoring system. At the
moment we are using munin. However, by default munin access is not
authenticated. 


# Prerequisites

## Step 1 — Creating the Password File

Before doing anything, you’ll need to create a password file which will be
storing your username and password. Here, we make user of openssl utilities,
and usually they are installed on the ubuntu system. Alternatively, you can use
the purpose-made htpasswd utility included in the apache2-utils package (Nginx
password files use the same format as Apache). Choose the method below that you
like best. Alternatively, htpassword tool can be used, this tools is included
in apache2-utils package. (is is Apache but generated password is compatible
with nginx).


### Option 1 — Creating the Password File Using the OpenSSL Utilities

If you have openssl installed, you’d not need to get ` htpassword` apache2
utility, openssl will just work fine.  \ First, create a ` .htpasswd` file on
/etc/nginx directory. This file will be storing your creds. Use the command
below to add user admin 
```
sudo sh -c "echo -n 'admin:' >> /etc/nginx/.htpasswd"
```
To include encrypted password for user admin, run the command below 

```
sudo sh -c "openssl passwd -apr1 >> /etc/nginx/.htpasswd"
```
### Option 2 - Creating username and password using apache2 utils 

#### install apache2 utils 

```
sudo apt update
sudo apt install apache2-utils
```

* The apache2-utils packages installs` htpasswd `command, which can be used to
  create` .htpasswd` file that nginx will be using to authenticate users to
  munin monitoring. 
* create hidden files` .htpaswd` on /etc/nginx directory
* The first time using` htpasswd `command will be with` -c, `enabling creating
  of the hidden` htpasswd` file.` `

```
sudo htpasswd -c /etc/nginx/.htpasswd Admin
```

* That will prompt for the password for the user Admin
* Leave -c when creating subsequent users, the file /etc/nginx/.htpasswd was
  creating first time you ran the command.

```
sudo htpasswd /etc/nginx/.htpasswd another_user
```

## Step 2 - Configuring nginx for password authentication.

Now, the file with users and password is created with logings on
/etc/nginx/.htpasswd. Next is to configure nginx to use the logins
authentication users to the munin monitoring tool. This will be enabled by
finding  munin location configuration and adding  configuration directives
enabling basic authentication. 

The line look like below, 

```
auth_basic "Restricted Content";
    	auth_basic_user_file /etc/nginx/.htpasswd;
```
