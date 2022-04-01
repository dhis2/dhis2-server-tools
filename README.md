# dhis2-server-tools
Tools to support installation and management of DHIS2
# Directory Structure

├── docs
│      ├── doc-1
│      ├── doc-2 
│      └── doc-n
└── deploy
         ├── cache/
         ├── vars/
             ├──containers.yml(jso
             └── other_global_vars
         ├── inventory/
             └── hosts
         ├── roles/
             ├── dhis2_instances
             ├── posgres
             ├── proxy
             └── munin
         ├──ansible.cfg
         ├── playbook-1.yml
         └── playbook-n.yaml
