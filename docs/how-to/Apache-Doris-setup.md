# Doris Setup 
### Pre-requisites
- Ubuntu24.04 server 
- ssh access to the server with non root user with sudo privileges 

### Preparing the environment 
#### LXC Container 

Please set the maximum number of open file descriptors larger than 60000

vi /etc/security/limits.conf 
* soft nofile 1000000
* hard nofile 1000000
Start be

Modify the number of virtual memory areas

sysctl -w vm.max_map_count=2000000 # set on the host if using lxd


### Step1: Login to the server via ssh and install java8 

```
ssh server_ip -p <ssh_port>
sudo apt update -y 
sudo apt upgrade -y 
sudo apt install openjdk-17-jre-headless 
```

### Step2: Disable swap on the host 
To disable swap temporarily (swap will be re-enabled after a restart):

```
swapoff -a
```

To permanently disable swap, edit /etc/fstab and comment out the swap partition entry, then restart the machine:

```
# /etc/fstab
# <file system>        <dir>         <type>    <options>             <dump> <pass>
tmpfs                  /tmp          tmpfs     nodev,nosuid          0      0
/dev/sda1              /             ext4      defaults,noatime      0      1
# /dev/sda2              none          swap      defaults              0      0
/dev/sda3              /home         ext4      defaults,noatime      0      2
```

### Step3: Add doris User
  
```
sudo adduser --comment "Doris Application User" --home  /usr/local/doris --disabled-login --system doris
```
### Step4: switch to doris user  

```
sudo su -l doris -s /bin/bash 
```

### Step5: Download  app binaries application

```
# version 3.0.5
wget https://apache-doris-releases.oss-accelerate.aliyuncs.com/apache-doris-3.0.5-bin-x64.tar.gz
```

### Step6: Extract Doris 

```
tar -xvzf ./apache-doris-3.0.5-bin-x64.tar.gz
```

### Step7: Edit both `doris/fe.conf`  and `be.conf` and set `JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"`

```
vim fe/conf/fe.conf
```

start fe

```
./fe/bin/start_fe.sh --daemo
```

### Add systemd services for backeknd and frontend 
#### frontend  `vim /etc/systemd/system/doris-fe.service`

```
[Unit]
Description=Apache Doris Frontend (FE)
After=network.target

[Service]
Type=forking
User=doris
WorkingDirectory=/usr/local/doris/fe
ExecStart= /usr/local/doris/fe/bin/start_fe.sh --daemon
ExecStop=/usr/local/doris/fe/bin/stop_fe.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### backend service `/etc/systemd/system/doris-be.service`

```
[Unit]
Description=Apache Doris Backend (BE)
# After=doris-fe.service
After=network-online.target

[Service]
Type=forking
User=doris
LimitCORE=infinity
LimitNOFILE=200000
WorkingDirectory=/usr/local/doris/be
ExecStart=/usr/local/doris/be/bin/start_be.sh --daemon
ExecStop=/usr/local/doris/be/bin/stop_be.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```



### Connecting to apache Doris using mysql ( not strictly required  )
To register BE node in Doris, you’ll need mysql client to connect to doris 
Install mysql client with 
`apt install mysql-client-core-8.0`
Login with mysql 

`mysql -uroot -P9030 -h127.0.0.1`
`ALTER SYSTEM ADD BACKEND "127.0.0.1:9050";`


### Configure DHIS2 to connect to Dorirs for Analytics 


```
# Analytics database management system
analytics.database = doris

# Analytics database JDBC driver class
analytics.connection.driver_class = com.mysql.cj.jdbc.Driver

# Analytics database connection URL
analytics.connection.url = jdbc:mysql://172.19.2.40:9030/analytics

# Analytics database username
analytics.connection.username = <doris_user>

# Analytics database password
analytics.connection.password = <doris_database_password>
```

### PosgresqlJAR




