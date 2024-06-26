# Starting a Khulnasoft Cluster

***Note:** Khulnasoft does not offer support for Docker or any orchestration platforms like Kubernetes, Docker Swarm, Apache Mesos, etc. Support covers only the published Khulnasoft Docker images. At this time, we strongly recommend that only very experienced and advanced customers use Docker to run Khulnasoft clusters.*

While Khulnasoft does not support orchestrators or the YAML templates required to deploy and manage clusters and other advanced configurations, we provide several examples of these different configurations in the "test_scenarios" folder. These are for prototyping purposes only.

One of the most common configurations of Khulnasoft Enterprise is the C3 configuration
(see [Khulnasoft Validated Architectures](https://www.khulnasoft.com/pdfs/white-papers/khulnasoft-validated-architectures.pdf) for more info).
This architecture contains a search head cluster, an index cluster, with a deployer and cluster master.

You can create a simple cluster with Docker Swarm using the following command:
```
 $> KHULNASOFT_COMPOSE=cluster_absolute_unit.yaml make sample-compose-up
```
The provisioning process will run for a few minutes after this command completes, while the Ansible plays run. This configuration is resource-intensive, so running this on your laptop may cause it to overheat and slow down.

To view port mappings run:
```
 $> docker ps
```
After several minutes, you should be able to log into one of the search heads `sh#` using the default username `admin` and the password you input at installation, or set through the Khulnasoft UI.

Once finished, you can remove the cluster by running:
```
 $> KHULNASOFT_COMPOSE=cluster_absolute_unit.yaml make sample-compose-down
```

The `cluster_absolute_unit.yaml` file located in the test_scenarios folder is a
Docker Compose file that can be used to mimic this type of deployment.

```
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true
```

`version 3.6` is a reference to the Docker Compose version, while `networks` is a reference to the type of adapter that will be created for the Khulnasoft deployment to communicate across. For more information on the different types of network drivers, consult your Docker installation manual.

In `cluster_absolute_unit.yaml`, all instances of Khulnasoft Enterprise are created under one major service object.

```
services:
  sh1:
    networks:
      khulnasoftnet:
        aliases:
          - sh1
    image: khulnasoft/khulnasoft:latest
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3,idx4
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_search_head_captain
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_LICENSE_URI=<license uri> http://foo.com/khulnasoft.lic
      - DEBUG=true
    ports:
      - 8000
    volumes:
      - ./defaults:/tmp/defaults
```
It's important to understand how Docker knows how to configure each major container. Below is the above template broken down into its simplest components:

```
services:
  <hostname of container>:
    networks:
      <name of network created in the first section>:
        aliases:
          - <a short name to reference this container>
    image: <what image to use for creating this container>
    hostname: <actual hostname of the container to use>
    container_name: <labeling the container>
    environment:
      - KHULNASOFT_START_ARGS=--accept-license <required in order to start container>
      - KHULNASOFT_INDEXER_URL=<list of each indexer's hostname>
      - KHULNASOFT_SEARCH_HEAD_URL= <list of each search head's hostname>
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=<hostname of which container to make the captain>
      - KHULNASOFT_CLUSTER_MASTER_URL=<hostname of the cluster master>
      - KHULNASOFT_ROLE=<what role to use for this container>
      - KHULNASOFT_DEPLOYER_URL=<hostname of the deployer>
      - KHULNASOFT_LICENSE_URI=<uri to your Khulnasoft Enterprise license>
      - DEBUG=<true/false>
    ports:
      - 8000 <port to expose to the host>
    volumes:
      - ./defaults:/tmp/defaults <only used for volume mapping a default.yml>

```

Acceptable roles for KHULNASOFT_ROLE are as follows:
* khulnasoft_standalone
* khulnasoft_search_head
* khulnasoft_indexer
* khulnasoft_deployer
* khulnasoft_license_master
* khulnasoft_cluster_master
* khulnasoft_heavy_forwarder

For more information about these roles, refer to the [Khulnasoft Splexicon](https://docs.khulnasoft.com/splexicon).

After creating a Compose file, you can start an entire cluster with `docker-compose`:
```
docker-compose -f cluster_absolute_unit.yaml up -d
```

To support Khulnasoft Enterprise's complex configurations, the Docker container utilizes Ansible which performs the required provisioning commands. You can use the `docker log` command to follow these logs.

`docker ps` will show a list of all the current running instances on this node. The cluster master gives the best indication of cluster health without needing to check every container.
```
$ docker ps
```
```
CONTAINER ID        IMAGE                    COMMAND                  CREATED             STATUS                             PORTS                                                                                      NAMES
69ed0d45a50b        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 8 seconds (health: starting)    4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32776->8000/tcp   idx2
760c4a8661dd        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 9 seconds (health: starting)    4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32775->8000/tcp   dep1
d6013cce3dfc        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 9 seconds (health: starting)    4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32773->8000/tcp   sh3
6b8da3c05e24        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 9 seconds (health: starting)    4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32774->8000/tcp   sh2
bbbe650dd544        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 9 seconds (health: starting)    4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32772->8000/tcp   cm1
46bc515059d5        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 9 seconds (health: starting)    4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32771->8000/tcp   sh1
b68d8215d00a        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 10 seconds (health: starting)   4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32770->8000/tcp   idx4
8b934acb20b5        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 10 seconds (health: starting)   4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32769->8000/tcp   idx1
9df560952f17        khulnasoft-debian-9:latest   "/sbin/entrypoint.sh…"   11 seconds ago      Up 10 seconds (health: starting)   4001/tcp, 8065/tcp, 8088-8089/tcp, 8191/tcp, 9887/tcp, 9997/tcp, 0.0.0.0:32768->8000/tcp   idx3
```
Follow the stdout from the cluster master by running the following command:
```
docker logs -f <container-id>
```
In the above example, the container id is `bbbe650dd544`. So, the `docker logs` command would be run as follows:
```
docker logs -f bbbe650dd544
```
As Ansible runs, the results from each play can be seen on the screen, as well as written to an `ansible.log` file stored inside the container.

<!-- {% raw %} -->
```
PLAY [localhost] ***************************************************************

TASK [Gathering Facts] *********************************************************
Wednesday 29 August 2018  09:27:06 +0000 (0:00:00.070)       0:00:00.070 ******
ok: [localhost]

TASK [include_role : Khulnasoft_upgrade] *******************************************
Wednesday 29 August 2018  09:27:08 +0000 (0:00:02.430)       0:00:02.501 ******

TASK [include_role : {{ khulnasoft_role }}] ****************************************
Wednesday 29 August 2018  09:27:09 +0000 (0:00:00.137)       0:00:02.638 ******

TASK [Khulnasoft_common : Install Khulnasoft] ******************************************
Wednesday 29 August 2018  09:27:09 +0000 (0:00:00.378)       0:00:03.016 ******
changed: [localhost]

TASK [Khulnasoft_common : Install Khulnasoft (Windows)] ********************************
Wednesday 29 August 2018  09:28:29 +0000 (0:01:20.307)       0:01:23.324 ******

TASK [Khulnasoft_common : Generate user-seed.conf] *********************************
Wednesday 29 August 2018  09:28:29 +0000 (0:00:00.123)       0:01:23.447 ******
changed: [localhost] => (item=USERNAME)
changed: [localhost] => (item=PASSWORD)
```
<!-- {% endraw %} -->

Once Ansible has finished running, a summary screen will be displayed.

<!-- {% raw %} -->
```
PLAY RECAP *********************************************************************
localhost                  : ok=12   changed=6    unreachable=0    failed=1
`
Wednesday 29 August 2018  09:31:56 +0000 (0:00:01.435)       0:04:49.684 ******
===============================================================================
Khulnasoft_common : Start Khulnasoft ------------------------------------------ 105.37s
Khulnasoft_common : Download Khulnasoft license -------------------------------- 83.32s
Khulnasoft_common : Install Khulnasoft ----------------------------------------- 80.31s
Khulnasoft_common : Apply Khulnasoft license ------------------------------------ 6.31s
Khulnasoft_common : Enable the Khulnasoft-to-Khulnasoft port ------------------------ 6.26s
Gathering Facts --------------------------------------------------------- 2.43s
Khulnasoft_cluster_master : Set indexer discovery --------------------------- 1.44s
Khulnasoft_common : include_tasks ------------------------------------------- 1.42s
Khulnasoft_common : Generate user-seed.conf --------------------------------- 0.69s
Khulnasoft_common : Set license location ------------------------------------ 0.59s
include_role : {{ Khulnasoft_role }} ---------------------------------------- 0.37s
Khulnasoft_common : include_tasks ------------------------------------------- 0.22s
Khulnasoft_cluster_master : Get indexer count ------------------------------- 0.18s
Khulnasoft_cluster_master : Get default replication factor ------------------ 0.18s
Khulnasoft_common : Set as license slave ------------------------------------ 0.17s
include_role : Khulnasoft_upgrade ------------------------------------------- 0.14s
Khulnasoft_common : Install Khulnasoft (Windows) -------------------------------- 0.12s
Khulnasoft_cluster_master : Lower indexer search/replication factor --------- 0.10s
Stopping Khulnasoftd...
Shutting down. Please wait, as this may take a few minutes.
..
Stopping Khulnasoft helpers...

Done.
```
<!-- {% endraw %} -->

It's important to call out the `RECAP` line, as it's the biggest indicator of whether Khulnasoft Enterprise was configured correctly. In this example, there was a failure during container creation. The offending play is:

```
TASK [Khulnasoft_cluster_master : Set indexer discovery] ***************************
Wednesday 29 August 2018  09:31:54 +0000 (0:00:00.101)       0:04:48.249 ******
fatal: [localhost]: FAILED! => {"cache_control": "private", "changed": false, "connection": "Close", "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<response>\n  <messages>\n    <msg type=\"ERROR\">Unauthorized</msg>\n  </messages>\n</response>\n", "content_length": "130", "content_type": "text/xml; charset=UTF-8", "date": "Wed, 29 Aug 2018 09:31:56 GMT", "msg": "Status code was 401 and not [201, 409]: HTTP Error 401: Unauthorized", "redirected": false, "server": "Khulnasoftd", "status": 401, "url": "https://127.0.0.1:8089/servicesNS/nobody/system/configs/conf-server", "vary": "Cookie, Authorization", "www_authenticate": "Basic realm=\"/Khulnasoft\"", "x_content_type_options": "nosniff", "x_frame_options": "SAMEORIGIN"}
	to retry, use: --limit @/opt/ansible/ansible-retry/site.retry
```

In the above example, the `default.yml` file didn't contain a password, nor was an environment variable set.

See the [troubleshooting](TROUBLESHOOTING.md) section for more common issues that can occur. There you will also find instructions for producing Khulnasoft diagnostics for support such as `khulnasoft diag`, as well as instructions for downloading the full Khulnasoft `ansible.log` file.
