# Ansible Activemq Artemis
[![Build Status](https://travis-ci.org/remyma/ansible-artemis.svg?branch=master)](https://travis-ci.org/remyma/ansible-artemis)

Install and configure activemq artemis broker.

## Requirements

* *java* : artemis needs java to run.

## Role Variables

### Service configuration

| Variable     | type | Default       | Description    |
| ------------ | ---- |------------- | -------------- |
| artemis_version | string | ```2.6.0``` | Artemis version |
| artemis_download_url | string | | Download Artemis archive url |
| artemis_group | dictionnary | see defaults| Artemis service group |
| artemis_user | dictionnary | see defaults | Artemis service user |
| artemis_install_dir | string | ```/opt``` | Artemis installation directory |
| artemis_home | string | ```{{ artemis_install_dir }}/apache-artemis-{{ artemis_version }}``` | Artemis home directory |
| artemis_brokers | list | see defaults | List of brokers to install (you can install multiple instances if you want to) |

### Broker instance default configuration

| Variable     | type | Default       | Description    |
| ------------ | ---- |------------- | -------------- |
| artemis_home | string | ```/opt/artemis``` (symlink to system current) | ARTEMIS_HOME in etc/artemis.profile |
| artemis_host | string | ```0.0.0.0``` | Artemis host |
| artemis_port_artemis | number | 61616 | Tcp port |
| artemis_port_amqp | number | 5672| Amqp port |
| artemis_port_stomp | number | 61613 | Stomp port |
| artemis_port_hornetq | number | 5445 | HornetQ port |
| artemis_port_mqtt | number | 1883 | Mqtt port |
| artemis_acceptors | list | see defaults | List of artemis acceptors for the broker (amqp, mqtt, ...) |
| artemis_web_port | number | 8161 | http web port (used for jolokia, console ui) |
| artemis_web_host | string | localhost | http web port (used for jolokia, console ui) |
| jolokia_cors | list of strings | ["*://localhost*"] | CORS Allow-Origin policy for jolokia |
| artemis_journal_type | string | NIO | Journal type |
| artemis_journal_pool_files | string | 10 | Upper threshold of the journal file pool |
| artemis_journal_buffer_timeouts | dict | {NIO: "3333333" ASYNCIO: "500000"} | Artemis defaults for journal-buffer-timeout, depending on journal-type |

## Example Playbook

### Basic install

```yaml
    - hosts: artemis-servers
      roles:
        - { role: artemis }
```

### Multi-instances

```yaml
    - hosts: artemis-servers
      roles:
        - { role: artemis }
```

## License

BSD
