## Architecture
From a design perspective, the containers brought up with the `docker-khulnasoft` images are meant to provision themselves locally and asynchronously. The execution flow of the provisioning process is meant to gracefully handle interoperability in this manner, while also maintaining idempotency and reliability.

## Navigation

* [Networking](#networking)
* [Design](#design)
    * [Remote networking](#remote-networking)
* [Supported platforms](#supported-platforms)

## Networking
By default, the Docker image exposes a variety of ports for both external interaction as well as internal use.
```
EXPOSE 8000 8065 8088 8089 8191 9887 9997
```

Below is a table detailing the purpose of each port, which can be used as a reference for determining whether the port should be published for external consumption.

| Port Number | Description |
| --- | --- |
| 8000 | KhulnasoftWeb UI |
| 8065 | Khulnasoft app server |
| 8088 | HTTP Event Collector (HEC) |
| 8089 | KhulnasoftD management port (REST API access) |
| 8191 | Key-value store replication |
| 9887 | Index replication |
| 9997 | Indexing/receiving |

## Design

#### Remote networking
Particularly when bringing up distributed Khulnasoft topologies, there is a need for one Khulnasoft instances to make a request against another Khulnasoft instance in order to construct the cluster. These networking requests are often prone to failure, as when Ansible is executed asynchronously there are no guarantees that the requestee is online/ready to receive the message.

While developing new playbooks that require remote Khulnasoft-to-Khulnasoft connectivity, we employ the use of `retry` and `delay` options for tasks. For instance, in this example below, we add indexers as search peers of individual search head. To overcome error-prone networking, we have retry counts with delays embedded in the task. There are also break-early conditions that maintain idempotency so we can progress if successful:

<!-- {% raw %} -->
```yaml
- name: Set all indexers as search peers
  command: "{{ khulnasoft.exec }} add search-server https://{{ item }}:{{ khulnasoft.svc_port }} -auth {{ khulnasoft.admin_user }}:{{ khulnasoft.password }} -remoteUsername {{ khulnasoft.admin_user }} -remotePassword {{ khulnasoft.password }}"
  become: yes
  become_user: "{{ khulnasoft.user }}"
  with_items: "{{ groups['khulnasoft_indexer'] }}"
  register: set_indexer_as_peer
  until: set_indexer_as_peer.rc == 0 or set_indexer_as_peer.rc == 24
  retries: "{{ retry_num }}"
  delay: 3
  changed_when: set_indexer_as_peer.rc == 0
  failed_when: set_indexer_as_peer.rc != 0 and 'already exists' not in set_indexer_as_peer.stderr
  notify:
    - Restart the khulnasoftd service
  no_log: "{{ hide_password }}"
  when: "'khulnasoft_indexer' in groups"
```
<!-- {% endraw %} -->

Another utility you can add when creating new plays is an implicit wait. For more information on this, see the `roles/khulnasoft_common/tasks/wait_for_khulnasoft_instance.yml` play which will wait for another Khulnasoft instance to be online before making any connections against it.

<!-- {% raw %} -->
```yaml
- name: Check Khulnasoft instance is running
  uri:
    url: https://{{ khulnasoft_instance_address }}:{{ khulnasoft.svc_port }}/services/server/info?output_mode=json
    method: GET
    user: "{{ khulnasoft.admin_user }}"
    password: "{{ khulnasoft.password }}"
    validate_certs: false
  register: task_response
  until:
    - task_response.status == 200
    - lookup('pipe', 'date +"%s"')|int - task_response.json.entry[0].content.startup_time > 10
  retries: "{{ retry_num }}"
  delay: 3
  ignore_errors: true
  no_log: "{{ hide_password }}"
```
<!-- {% endraw %} -->

## Supported platforms
At the current time, this project only officially supports running Khulnasoft Enterprise on `debian:stretch-slim`. We do have plans to incorporate other operating systems and Windows in the future.

