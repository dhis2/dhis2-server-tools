# Reverse Proxy 

## Introduction

It is a common practice running web applications behind a reverse proxy server.
This is also the case with apache2 tomcat based web app. Reverse proxy is an
entry point (ingress) to dhis2 infrastructure and it does more than just proxy
forwarding to the backend. Amongst other benefits, proxy does the following 

* improve security by acting as an intermediary between you backing app and your clients. 
* It is a prerequisite to load balancing configuration. 
* static content caching
* SSL/TLS termination 
* ReverseProxy requests routing. 
* URL Rewriting and Redirection

We do support two proxy software at the moment, nginx and apache2. Apache2 is
open source, but nginx is partially open source in the sense that there are
other plugins that you’ll need to buy to use. This guide serves as a reference
guideline on how you can generally set up a proxy instance in your server farm. 

## Prerequisites 

* An ubuntu 20.04/22.04 server 
* non root user with ssh access and sudo rights
* good internet connection
* Initiated lxd cluster (optional)

## Required software 

* proxy (apache, nginx)

## The install 

### Step1 - Create container 

This step is not necessary if you have a dedicated proxy server. Skip it if
thats the case for your deployment. 

### Step2 - Update and upgrade 

```
sudo apt update -y
sudo apt upgrade -y 
```

### Step2 -  Install reverse proxy web application

Its your choice to decide on the proxy software to use. There are many choices
out there and there one we are supooring are nginx and apache2. HAProxy for
example is groing popular and we might consider supporting it in our future
plan. 

### Step2  SSL/Certificate

One of the important role of the apache2 proxy is TLS Termination. TLS makes
use of a pair of TLS certificate and TLS key. Usually this can be purchased
prior for your sub domain. However, you do not worry if you do not have one
already, there are sites that yuo can use to generate these Cryptographic
resources provided you can authenticate if you are really the owner of you
domain. One of them is letsecnrypt. 

For automated certificate generation, we

##  step - Proxy software install and config 

nginx Install and configuration 

Apache Install and configuration

### Step 2: Firewall configuration,

Firewall needs to be configured to allow port 80 and 443 , 

* In cases of using lxd containers, this will need to  be configures also on
host uncomplicated firewall (UFW)
* 

### Step4: Install reverse proxy web application

There are two kinds of reverse proxy apps we are supporting. 

1. apache2 
2. nginx 

To install apache2 run sudo apt i

We are using apt package management tool installing system packages here. 

Setting up nginx proxy 

sudo apt install nginx 

This comes with default conguration which needs to be customized for security. 

We delete nginx  config that comes with the install 

disable nginx version show

add our custom nginx conguration 

add custom location configuration for dhis2 munin and glowroot monitoring. 

### Proxy setup with apache2

install apache2 server 

delete custom configuration 

add our custom configuration for the ghost

add custom configuration for upstream dhis2 munin and glowroot 

Step5: Certbot

We do TLS offloading on proxy level. One of thei items required for this is the
certificate and key. In some deployments, there is SSL certificate and in
others there is not Certifiate provided. We therefore support two scenarions

1. Letencrypt 
2. CustomSSl 

Step5: Main config file 

There are templates for vhost configuration files for both nginx and apache2.
Items that are inserted into these templates are dormant names, and ssl/tls
cetificate location/. 

### Step6: location file

These files hold upstream configuration files that proxy pass requests to
dhis2, munin and glowroot application monitor.

These files are loaded from the main configuration file. 
 


