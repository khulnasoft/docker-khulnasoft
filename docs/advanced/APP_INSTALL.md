## Installing Khulnasoft Apps and Add-ons
The Khulnasoft Docker image supports the ability to dynamically install any Khulnasoft-compliant app or add-on. These can be certified apps that are hosted through [KhulnasoftBase](https://khulnasoftbase.khulnasoft.com/) or they might be local apps you have developed yourself.

App installation can be done a variety of ways: either through a file/directory volume-mounted inside the container, or through an external URL for dynamic downloads. Nothing is required for the former, and the environment variable `KHULNASOFT_APPS_URL` supports the latter.

**NOTE:** Installation of Khulnasoft Enterprise Security (ES) and Khulnasoft IT Service Intelligence (ITSI) is currently not supported with this image. Please contact Khulnasoft Services for more information on using these applications with Khulnasoft Enterprise in a container.

## Navigation

* [Volume-mount app directory](#volume-mount-app-directory)
* [Download via URL](#download-via-url)
* [Multiple apps](#multiple-apps)
* [Apps in distributed environments](#apps-in-distributed-environments)

## Volume-mount app directory
If you have a local directory that follows the proper Khulnasoft apps model, you can mount this entire path to the container at runtime.

For instance, take the following app `khulnasoft_app_example`:
```bash
$ find . -type f
./khulnasoft_app_example/default/app.conf
./khulnasoft_app_example/metadata/default.meta
```

We can bind-mount this upon container start and use it as a regular Khulnasoft app:
```bash
# Volume-mounting option using --volumes/-v flag
$ docker run -it -v "$(pwd)/khulnasoft_app_example:/opt/khulnasoft/etc/apps/khulnasoft_app_example/" --name so1 --hostname so1 -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" -e "KHULNASOFT_START_ARGS=--accept-license" -it khulnasoft/khulnasoft:latest

# Volume-mounting option using --mount flag
$ docker run -it --mount type=bind,source="$(pwd)"/khulnasoft_app_example,target=/opt/khulnasoft/etc/apps/khulnasoft_app_example/ --name so1 --hostname so1 -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" -e "KHULNASOFT_START_ARGS=--accept-license" -it khulnasoft/khulnasoft:latest
```

You should be able to view the `khulnasoft_app_example` in KhulnasoftWeb after the container successfully finished provisioning.

## Download via URL
In most cases, you're likely hosting the app as a tar file somewhere accessible in your network. This decouples the need for Khulnasoft apps and configuration files to exist locally on a node, which enables Khulnasoft to run in a container orchestration environment.

#### KhulnasoftBase apps
Please refer to this docker-compose.yml file for how to download KhulnasoftBase apps with authentication:

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_APPS_URL=https://khulnasoftbase.khulnasoft.com/app/2890/release/4.1.0/download
      - KHULNASOFTBASE_USERNAME=<sb-username>
      - KHULNASOFTBASE_PASSWORD=<sb-password>
      - KHULNASOFT_PASSWORD=<password>
    ports:
      - 8000
```

#### Self-hosted apps
Please refer to this docker-compose.yml file for how to download any app hosted at an arbitrary location:

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_APPS_URL=https://webserver/apps/app.spl
      - KHULNASOFT_PASSWORD=<password>
    ports:
      - 8000
```

#### Apps on filesystem
If you build your own image on top of the `khulnasoft/khulnasoft` or `khulnasoft/universalforwarder` image, it's possible you may embed a tar file of an app inside. Or, you can go with the bind-mount volume approach and inject a tar file on container run time. In either case, it's still possible to install an app from this file on the container's filesystem with the following.

Please refer to this docker-compose.yml file for how to install an app in the container's filesystem:

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_APPS_URL=/tmp/app.tgz
      - KHULNASOFT_PASSWORD=<password>
    ports:
      - 8000
```

## Multiple apps
As one would expect, Khulnasoft can and should support downloading any combination or series of apps. This can be incredibly useful when cross-referencing data from various sources.

The `KHULNASOFT_APPS_URL` supports multiple apps, as long as they are comma-separated. Refer to this `docker-compose.yml` file for how to install multiple apps:

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_APPS_URL=/tmp/app.tgz,https://webserver/apps/app.spl,https://khulnasoftbase.khulnasoft.com/app/2890/release/4.1.0/download
      - KHULNASOFTBASE_USERNAME=<sb-username>
      - KHULNASOFTBASE_PASSWORD=<sb-password>
      - KHULNASOFT_PASSWORD=<password>
    ports:
      - 8000
```

## Apps in distributed environments
This docker image also deploys apps when running Khulnasoft in distributed environments. There are, however, special cases and instructions for how apps get deployed in these scenarios.

In the case of multiple search heads (no clustering) and multiple indexers (no clustering), you will explicitly need to tell each container what apps to install by defining a `KHULNASOFT_APPS_URL` for each role. See the example below and note the different apps used for search heads and indexers:

```
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  sh1:
    networks:
      khulnasoftnet:
        aliases:
          - sh1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh1,sh2
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_APPS_URL=https://webserver/apps/appA.tgz
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  sh2:
    networks:
      khulnasoftnet:
        aliases:
          - sh2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: sh2
    container_name: sh2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh1,sh2
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_APPS_URL=https://webserver/apps/appA.tgz
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  idx1:
    networks:
      khulnasoftnet:
        aliases:
          - idx1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx1
    container_name: idx1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh1,sh2
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_APPS_URL=https://webserver/apps/appB.tgz,https://webserver/apps/appC.tgz
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  idx2:
    networks:
      khulnasoftnet:
        aliases:
          - idx2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx2
    container_name: idx2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh1,sh2
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_APPS_URL=https://webserver/apps/appB.tgz,https://webserver/apps/appC.tgz
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
```

In the case of search head clusters, you will explicitly need to tell the `khulnasoft_deployer` what apps to install by defining a `KHULNASOFT_APPS_URL` for that particular role. The deployer will manage the distribution of apps to each of the search head cluster members (search heads). See the example below and note the different apps used for search heads and indexers:


```
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  dep1:
    networks:
      khulnasoftnet:
        aliases:
          - dep1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: dep1
    container_name: dep1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_ROLE=khulnasoft_deployer
      - KHULNASOFT_APPS_URL=https://webserver/apps/appA.tgz,https://webserver/apps/appB.tgz
    ports:
      - 8000

  sh1:
    networks:
      khulnasoftnet:
        aliases:
          - sh1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_ROLE=khulnasoft_search_head_captain
    ports:
      - 8000

  sh2:
    networks:
      khulnasoftnet:
        aliases:
          - sh2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: sh2
    container_name: sh2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_ROLE=khulnasoft_search_head
    ports:
      - 8000

  sh3:
    networks:
      khulnasoftnet:
        aliases:
          - sh3
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: sh3
    container_name: sh3
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_ROLE=khulnasoft_search_head
    ports:
      - 8000

  idx1:
    networks:
      khulnasoftnet:
        aliases:
          - idx1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx1
    container_name: idx1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_ROLE=khulnasoft_indexer
    ports:
      - 8000

  idx2:
    networks:
      khulnasoftnet:
        aliases:
          - idx2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx2
    container_name: idx2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_DEPLOYER_URL=dep1
      - KHULNASOFT_ROLE=khulnasoft_indexer
    ports:
      - 8000
```

In the case of indexer clusters, you will explicitly need to tell the `khulnasoft_cluster_master` what apps to install by defining a `KHULNASOFT_APPS_URL` for that particular role. The cluster master will manage the distribution of apps to each of the indexer cluster members (indexers). See the example below and note the different apps used for search heads and indexers:

```
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  sh1:
    networks:
      khulnasoftnet:
        aliases:
          - sh1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  cm1:
    networks:
      khulnasoftnet:
        aliases:
          - cm1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: cm1
    container_name: cm1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_cluster_master
      - KHULNASOFT_APPS_URL=https://webserver/apps/appA.tgz,https://webserver/apps/appB.tgz
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  idx1:
    networks:
      khulnasoftnet:
        aliases:
          - idx1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx1
    container_name: idx1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  idx2:
    networks:
      khulnasoftnet:
        aliases:
          - idx2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx2
    container_name: idx2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_PASSWORD
    ports:
      - 8000

  idx3:
    networks:
      khulnasoftnet:
        aliases:
          - idx3
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: idx3
    container_name: idx3
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh1,sh2,sh3
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
```
