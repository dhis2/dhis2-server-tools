# Doris Setup Guide

## Prerequisites

- Ubuntu 24.04 Server
- SSH access using a non-root user with `sudo` privileges

---

## Step 1: Prepare the Environment

> **Note:**  
> If Doris is running inside an LXD container, apply the following configurations on the **LXD host**.

### Increase the Number of Open File Descriptors

Edit `/etc/security/limits.conf`:

```bash
vim /etc/security/limits.conf
```

Add the following lines:

```
* soft nofile 1000000
* hard nofile 1000000
```

### Increase the Virtual Memory Area Limit

```bash
sysctl -w vm.max_map_count=2000000
```

---

## Step 2: Disable Swap on the Host

To temporarily disable swap (reverts on reboot):

```bash
sudo swapoff -a
```

To disable swap permanently, edit `/etc/fstab` and comment out the swap entry:

```bash
sudo vim /etc/fstab
```

Example:

```bash
# <file system>        <dir>         <type>    <options>             <dump> <pass>
tmpfs                  /tmp          tmpfs     nodev,nosuid          0      0
/dev/sda1              /             ext4      defaults,noatime      0      1
# /dev/sda2            none          swap      defaults              0      0
/dev/sda3              /home         ext4      defaults,noatime      0      2
```

Then reboot the machine.

---

## Step 3: Install Java 17 (Required for Doris 3.0.x)

```bash
ssh <server_ip> -p <ssh_port>
sudo apt update && sudo apt upgrade -y
sudo apt install openjdk-17-jre-headless -y
```

---

## Step 4: Create a Dedicated Doris User

```bash
sudo adduser --comment "Doris Application User" --home /usr/local/doris --disabled-login --system doris
```

---

## Step 5: Switch to the Doris User

```bash
sudo su -l doris -s /bin/bash
```

---

## Step 6: Download Doris Binaries

```bash
# Example: version 3.0.5
wget https://apache-doris-releases.oss-accelerate.aliyuncs.com/apache-doris-3.0.5-bin-x64.tar.gz
```

---

## Step 7: Extract the Archive

```bash
tar -xvzf apache-doris-3.0.5-bin-x64.tar.gz
```

---

## Step 8: Configure `fe.conf` and `be.conf`

Set the `JAVA_HOME` environment variable in both config files:

```bash
# For Frontend
vim fe/conf/fe.conf
```

Add or update:

```
JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
```

Repeat similarly for `be/conf/be.conf`.

---

## Step 9: Start the Frontend

```bash
./fe/bin/start_fe.sh --daemon
```

---

## Step 10: Create systemd Services for Doris

### Doris Frontend (`/etc/systemd/system/doris-fe.service`)

```ini
[Unit]
Description=Apache Doris Frontend (FE)
After=network.target

[Service]
Type=forking
User=doris
WorkingDirectory=/usr/local/doris/fe
ExecStart=/usr/local/doris/fe/bin/start_fe.sh --daemon
ExecStop=/usr/local/doris/fe/bin/stop_fe.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Doris Backend (`/etc/systemd/system/doris-be.service`)

```ini
[Unit]
Description=Apache Doris Backend (BE)
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

Enable and start both services:

```bash
sudo systemctl enable doris-fe
sudo systemctl enable doris-be
sudo systemctl start doris-fe
sudo systemctl start doris-be
```

---

## Step 11: Connect to Doris via MySQL Client *(Optional)*

You’ll need the MySQL client to register a backend (BE) node:

```bash
sudo apt install mysql-client-core-8.0
```

Then connect:

```bash
mysql -uroot -P9030 -h127.0.0.1
```

Inside MySQL shell:

```sql
ALTER SYSTEM ADD BACKEND "127.0.0.1:9050";
```

---

## Step 12: Configure DHIS2 to Use Doris for Analytics

```properties
# Analytics database management system
analytics.database = doris

# JDBC driver
analytics.connection.driver_class = com.mysql.cj.jdbc.Driver

# Connection URL
analytics.connection.url = jdbc:mysql://172.19.2.40:9030/analytics

# Authentication
analytics.connection.username = <doris_user>
analytics.connection.password = <doris_database_password>
```

---

## Optional: PostgreSQL JDBC Driver

*(Add configuration or usage details here if needed.)*

