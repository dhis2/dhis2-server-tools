# Ansible Vault
## Introduction
Ansible-vault offers a secure solution for encrypting sensitive data, such as
usernames and passwords, used in your playbook. For example, when connecting to
servers via SSH and requiring elevated rights for certain tasks, supplying the
sudo password becomes necessary for privilege escalation. While you can use the
`-K` ansible directive to enter the sudo password, it becomes challenging if
each server has a different sudo password. The `-K` directive only accepts a
single variable or input, thus making it impractical in such scenarios.
Sensitive parameters like ssh and sudo passwords can be written into host
files, i.e in `inventory/host_vars/` directory, albeit the files must be
encrypted if you must conform to the best security standards. Nonetheless, its
not always a requirement to encrypt host files, there is no need if they do not
have any sensitive data. 


## What needs ansible-vault encryption in our deployment ?. 
Quick answer, files containing sensitive data.
More specifically

* munin logins
* database usernames and passwords
* sudo passwords (`ansible_become_pass`) if your deployments happens on
  different servers, implies ssh password as well, if you're not using key based
  authentication.  

The variables in Ansible can be stored in various locations. One approach is to
use host files in the `inventory/host_vars/` directory with the name
corresponding to the hostname as it appears in your `inventory/hosts` file. This
allows you to separate variables specific to each host. For example, if you
have a host named proxy, you can create an encrypted file in
`inventory/host_vars/proxy` to store proxy-specific variables. You have the
option to create an encrypted file on the fly or encrypt plain text files. To
learn more about variable precedence and where to store variables in Ansible,
you can refer to the [Ansible Documentation on Variable precedence
](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable)
. This will provide you with a deeper understanding of how Ansible handles
variables and where you should place them for optimal management.

## How to encrypt files with ansible-vault 
* **Option1**: Create encrypted files with ansible-vault command on the fly. 
  This is the recommended approach, that you create an encrypted vault already,
  rather than later.
  ```
  ansible-vault create inventory/host_vars/proxy
  ```
* **Option2**: Encrypt already created files with ansible vault.
  This approach is only good if you have files already created and you just
  want to enforce encryption.

  ```
  ansible-vault encrypt inventory/host_vars/proxy
  ```

In both scenarios, you will be prompted twice for encryption password, be sure
to save the password because you will later need it when accessing the vault.  To edit
the vault and add contents like variables, use

```
ansible-vault edit  inventory/host_vars/proxy
```

This will open the file for editing, with your available text editor, in my
experience `vim`. Put your variables like it's shown below
```
munin_users:
  - name: admin
    password: <put_secure_password>

# if you want munin access from non default base path  
munin_base_path: <base_path_for_munin>
# for privilege escalation if you are connecting via ssh with non root user and running tasks
# requring sudo access
ansible_become_pass: <strong_sudo_password> 

```

## Accessing the vault from the playbook
In Ansible, before executing any task, the playbook will load all variables,
including those stored in the `inventory/host_vars/` directory. If you have
encrypted files in this location, attempting to access them without decryption
will result in an error. To handle this situation, you can use the
`--ask-vault-password` flag during runtime. By providing the `--ask-vault-password`
flag, you will be prompted to enter your vault password, which will then be
used to decrypt the encrypted files and make the variables available for use in
the playbook. This allows for secure handling of sensitive information and
ensures that your playbook can access the necessary encrypted variables during
runtime.

```
ansible-playbook <your_playbook.y[a]ml> --ask-vault-password 
```

# Conlusion
Ansible Vault provides a secure solution for storing sensitive data in
encrypted files and using them with Ansible. By leveraging Ansible Vault, we
can safely store important information like ansible_become_pass, Munin
usernames, passwords, and other confidential data. For further details and
examples, you can refer to the official [Ansible Vault
documentation.](https://docs.ansible.com/ansible/latest/cli/ansible-vault.html)
