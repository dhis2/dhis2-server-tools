Table of Contents
---
<!-- vim-markdown-toc GFM -->

* [Ansible SSH Connection](#ansible-ssh-connection)
  * [SSH configuration](#ssh-configuration)
    * [Modifying ssh settings using `~/.ssh/config` file](#modifying-ssh-settings-using-sshconfig-file)
    * [Using ansible variables to override ssh defaults](#using-ansible-variables-to-override-ssh-defaults)
    * [Using prompts to ask ssh and sudo passwords](#using-prompts-to-ask-ssh-and-sudo-passwords)
    * [Using variables to store ssh and sudo passwords](#using-variables-to-store-ssh-and-sudo-passwords)
      * [Store SSH and sudo passwords in ansible-vault encrypted files.](#store-ssh-and-sudo-passwords-in-ansible-vault-encrypted-files)
    * [Using key-based ssh authentication to eliminate the need for ssh-password.](#using-key-based-ssh-authentication-to-eliminate-the-need-for-ssh-password)
  * [Testing the Ansible connection to managed hosts](#testing-the-ansible-connection-to-managed-hosts)
  * [Conclusion](#conclusion)

<!-- vim-markdown-toc -->

# Ansible SSH Connection
Ansible is an agentless automation tool, it therefore relies on some connection
mechanism to run tasks on the remote host. One of the ways that ansible
connects to the managed hosts is with ssh.<br> Consider a distributed deployment
architecture depicted below, 

![Alt text](./images/distributed-architecture.png?raw=true "Distributed")

In this setup, the playbooks will be executed from the ansible-controller
(deployment server ) and Ansible does the work via SSH.
This tutorial illustrates how to configure an SSH connection to make the
deployment process less dependent on human interaction. It achieves this by
utilizing SSH keys and Ansible variables.

## SSH configuration

By default, the SSH client comes with certain settings, such as the username
being the current logged-in user and the port being 22. These defaults can be modified in
the SSH configuration file, typically located at `~/.ssh/config`. Ansible
honors all this configurations.

### Modifying ssh settings using `~/.ssh/config` file
- Ansible respects and utilizes configurations specified in the SSH
  configuration file.

- Consider an example below. 
```
Host postgres
    hostname 172.19.2.20
    User ubuntu
    port 822
    IdentityFile ~/.ssh/id_rsa
```
- When you run an ansible playbook against host `postgres`, ansible will
  establish ssh connection to the hostname `172.19.2.20` with the  use username
  `ubuntu`, port `822` (non-default port) and IdentityFile `~/.ssh/id_rsa`.

### Using ansible variables to override ssh defaults

- Ansible allows for the configuration of SSH settings through variables, and
  these variables can be defined in various files, including the inventory
  file.
- Here are Ansible variables to modify SSH parameters.
  ```
  ansible_host
  ansible_port
  ansible_user
  ansible_private_key_file
  ansible_sudo_pass
  ansible_password
  ```

  This screenshot shows configuring variables for postgres host in inventory file.  
  ![Alt text](./images/ssh_connection.png?raw=true "ansible_connection")
- Some of these magic variables stores sensitive information and needs to be stored in files encrypted with `ansible-vault`
  e.g `ansible_sudo_pass` and `ansible_password`

### Using prompts to ask ssh and sudo passwords
- When ansible uses ssh as connection mechanism, it uses supported ssh
  authentication mechanism. For it to connect to the remote endpoints, username
  and password must be supplied, that is if you are not using key-based
  authentication. That implies that you have the user added on the remote
  system with the password authentication ssh login. The following is a
  description of some useful options that can be used for SSH authentication
  with

    ```
    -u <user>                     Set the connection user.
    -k, --ask-pass                Ask the password of the connection user.
    -K, --ask-become-pass         Ask for sudo password, intended for privilege escalation.
    ```
- If flags are used when running playbook, you will be prompted for ssh and
  sudo password as show on blow screenshot<br>
    ![Alt text](./images/ssh-and-sudo-prompt.png?raw=true "ssh")

### Using variables to store ssh and sudo passwords
####  Store SSH and sudo passwords in ansible-vault encrypted files. 
- Ansible variables can be defined in different file locations, inventory file
  being just one of them. <br>
  Refer to [Ansible
  Precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable)
- Consider this use case:<br> There is  host named `postgres` in your inventory.<br>
  Connection to this host is over ssh with the password. In order to run playbooks against this host, you'll
  need a way of telling ansible `ssh` and `sudo` passwords. (if you are installing packages).
- These variables are sensitive and they need to be stored encrypted 
- To achieve that, you will create an encrypted file with `ansible-vault` named
  `postgres` in `dhis2-server-tools/deploy/inventory/host_vars/postgres`
  directory and store `ansible_pass` and `ansible_sudo_pass` variables. 
- Ansible will the read those variables from the file and use them for ssh and privilege escalation. 
 
  ```
  ansible-vault create dhis2-server-tools/deploy/inventory/host_vars/postgres
  ```
  ![Alt text](./images/creating-vault-file.png?raw=true "ssh")
  ![Alt text](./images/ssh-and-sudo-passwords.png?raw=true "ssh")


- However, the variables in
  `dhis2-server-tools/deploy/inventory/host_vars/postgres` are specific to
  `postgres` host and will not apply to other hosts in your inventory. 
  Its typical use case is when you have different ssh and sudo password for your hosts. <br> 
  If your ssh and sudo password is the same for all hosts, make use of
  `dhis2-server-tools/deploy/inventory/group_vars/all` file. Variables defined
  in this file applies to all hosts <br>
  Create and encrypt it in `dhis2-server-tools/deploy/inventory/group_vars/all`<br>
  ```
  ansible-vault create dhis2-server-tools/deploy/inventory/group_vars/all
  ```
- Now, whenever you run your playbook, you should include `--ask-vault-pass` or
  `-vault-password-file /path/to/vault-password-file` if you have fault
  password stored in a file.-vault-password-file /path/to/vault-password-file
  This password will be used to decrypt encrypted variable files like
  `dhis2-server-tools/deploy/inventory/host_vars/all` in the above
  example. 
  ```
  cd dhis2-server-tools/deploy/
  ansible-playbook dhis2.yml --ask-vault-pass
  ```
  Read More on [Ansible Vault Official
  Documentation](https://docs.ansible.com/ansible/latest/cli/ansible-vault.html)
###  Using key-based ssh authentication to eliminate the need for ssh-password.
- Consider generating ssh-key without pass-phrase.
- Since connection will be happening from the deployment server, your private
  key should be stored there.
  - Generate the key with 
    ```
    ssh-key-gen
    ```
  - Upload the key with `ssh-copy-id` utility to all the managed hosts.
    ```
    ssh-copy-id -i /path/to/the/generated/private-key hostname  
    ```
- Nonetheless, you will still need to have a way of specifying `sudo` password

## Testing the Ansible connection to managed hosts
- After setting up you ssh connection between the ansible-controller and the
  backend hosts, you should test to ensure it works.
- ansible will be connecting to the hosts defined in the inventory file, using
  defined `ansible_connection`, which in this case is `ansible_connection=ssh` 
- Both password or key-based authentication can work. Use ansible ping module
  to test your connection to all the backend hosts except localhost (127.0.0.1)
- If you and using ssh keys, then you do not need `--ask-pass (-k)`
  ```
  cd dhis2-server-tools/deploy/
  ansible 'all:!127.0.0.1' -m ping --ask-pass
  ```
- If your ssh is working, you will see SUCCESS messages as show on below screenshot

  ![Alt text](./images/ping_pong.png?raw=true "ping pong")
## Conclusion
For complete automation, it's advisable to leverage variables stored in
vault-encrypted files and SSH keys for automating the SSH connection.
Employing ansible-vault becomes essential, particularly when dealing with
variables that contain sensitive information that should not be stored in
plaintext.

