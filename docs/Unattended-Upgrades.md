# Unattended-upgrades

## Introduction, 

To ensure the regular update and upgrade of your dhis2 server, it is essential
to set up and enable unattended-upgrades. Many users tend to overlook this
critical aspect and become complacent as long as the server is running. By
following these step-by-step instructions, you can ensure that your packages
are continuously updated and upgraded:

Note, if you have separated servers for proxy, dhis2 and database, you’ll need
to run replete these steps on all of them. 

### Step1 -Install Unattended-Upgrades:
First, make sure that the unattended-upgrades package is installed on your
server. You can do this by running the following command:
```
sudo apt-get install unattended-upgrades
```
### step2: - Configure Unattended-Upgrades:
Next, you need to configure the unattended-upgrades package. The configuration
file is usually located at /etc/apt/apt.conf.d/50unattended-upgrades. Open the
file using a text editor like nano or vim:
```
sudo vim /etc/apt/apt.conf.d/50unattended-upgrades
```

### step3: Customize the Configuration:
In the configuration file, you can customize the settings to suit your needs.
For example, you can specify the email address to receive notifications and set
the update interval. Make sure to review and adjust the configurations as per
your requirements.

### Step4: Enable and restart Unattended-Upgrades:
Once you have configured the settings, save the file and exit the text editor.
Now, enable the unattended-upgrades service using the following command:
```
sudo systemctl enable unattended-upgrades
sudo systemctl restart unattended-upgrades
```

# Ansible Playbook 
```
- hosts: 127.0.0.1 
  become: true
  gather_facts: true
  tasks:
    # install unattended-unattended package
    - name: "Install unattended upgrades package"
      ansible.builtin.apt:
        name: 
          - unattended-upgrades
          - update-notifier-common
        state: present

    # Switch on unattended updates  
    - name: "Enabling unattended-updates, APT::Periodic::Update-Package-Lists "
      ansible.builtin.lineinfile:
        dest: /etc/apt/apt.conf.d/20auto-upgrades
        regexp: '^#?APT::Periodic::Update' 
        line: 'APT::Periodic::Update-Package-Lists "1";'
      notify: restart unattended-upgrades
    
    # Switch on unattended upgrades
    - name: "Enabling unattended-upgrades, APT::Periodic::Unattended-Upgrade"
      ansible.builtin.lineinfile:
        dest:  /etc/apt/apt.conf.d/20auto-upgrades
        regexp: '^#?APT::Periodic::Unattended' 
        line: 'APT::Periodic::Unattended-Upgrade "1";'
      notify: restart unattended-upgrades
    
    # Switch on unattended package upgrades
    - name: "Enabling Package upgrades"
      ansible.builtin.lineinfile:
        dest: "/etc/apt/apt.conf.d/50unattended-upgrades"
        regexp: '.*"\$\{distro_id\}:\$\{distro_codename\}-updates";'
        line: "\t\"${distro_id}:${distro_codename}-updates\";"
        state: present 
      notify: restart unattended-upgrades
        
    # Ensure unused dependencies are removed from the system. 
    - name: "Enable remove unused deps in /etc/apt/apt.conf.d/50unattended-upgrades"
      ansible.builtin.lineinfile:
        dest: "/etc/apt/apt.conf.d/50unattended-upgrades"
        line: 'Unattended-Upgrade::Remove-Unused-Dependencies "true";'
        insertafter: '^//Unattended-Upgrade::Remove-Unused-Dependencies'
      notify: restart unattended-upgrades
```
