## Examples

The purpose of this section is to showcase a wide variety of examples on how the `docker-khulnasoft` project can be used.

Note that for more complex scenarios, we will opt to use a [Docker compose file](https://docs.docker.com/compose/compose-file/) instead of the CLI for the sake of readability.

## I want to...

* [Create a standalone](#create-standalone-from-cli)
    * [...with the CLI](#create-standalone-from-cli)
    * [...with a compose file](#create-standalone-from-compose)
    * [...with a Khulnasoft license](#create-standalone-with-license)
    * [...with HEC](#create-standalone-with-hec)
    * [...with any app](#create-standalone-with-app)
    * [...with a KhulnasoftBase app](#create-standalone-with-khulnasoftbase-app)
    * [...with SSL enabled](#create-standalone-with-ssl-enabled)
    * [...with a Khulnasoft Free license](#create-standalone-with-khulnasoft-free-license)
* [Create sidecar forwarder running as root](#create-sidecar-root-forwarder)
* [Create standalone and universal forwarder](#create-standalone-and-universal-forwarder)
* [Create heavy forwarder](#create-heavy-forwarder)
* [Create heavy forwarder and deployment server](#create-heavy-forwarder-and-deployment-server)
* [Create indexer cluster](#create-indexer-cluster)
* [Create search head cluster](#create-search-head-cluster)
* [Create indexer cluster and search head cluster](#create-indexer-cluster-and-search-head-cluster)
* [Enable root endpoint on KhulnasoftWeb](#enable-root-endpoint-on-khulnasoftweb)
* [More](#more)

## Create standalone from CLI
Execute the following to bring up your deployment:
```bash
$ docker run --name so1 --hostname so1 -p 8000:8000 \
              -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -it khulnasoft/khulnasoft:latest
```

## Create standalone from compose

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_PASSWORD
    ports:
      - 8000:8000
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create standalone with license
Adding a Khulnasoft Enterprise license can be done in multiple ways. Review the following compose files below to see how it can be achieved, either with a license hosted on a webserver or with a license file as a direct mount.

<details><summary markdown='span'><code>docker-compose.yml</code> - license from URL</summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_LICENSE_URI=http://company.com/path/to/khulnasoft.lic
      - KHULNASOFT_PASSWORD
    ports:
      - 8000:8000
```
</details><p></p>

<details><summary markdown='span'><code>docker-compose.yml</code> - license from file</summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_LICENSE_URI=/tmp/license/khulnasoft.lic
      - KHULNASOFT_PASSWORD
    ports:
      - 8000:8000
    volumes:
      - ./khulnasoft.lic:/tmp/license/khulnasoft.lic
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create standalone with HEC
To learn more about the HTTP Event Collector (HEC) and how to use it, see [Set up and use HTTP Event Collector](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Data/UsetheHTTPEventCollector).

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_HEC_TOKEN=abcd1234
      - KHULNASOFT_PASSWORD
    ports:
      - 8000:8000
      - 8088:8088
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

To validate HEC is provisioned properly and functional:
```bash
$ curl -k https://localhost:8088/services/collector/event -H "Authorization: Khulnasoft abcd1234" -d '{"event": "hello world"}'
{"text": "Success", "code": 0}
```

## Create standalone with app
Khulnasoft apps can also be installed using this Docker image.

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_APPS_URL=http://company.com/path/to/app.tgz
      - KHULNASOFT_PASSWORD
    ports:
      - 8000:8000
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create standalone with KhulnasoftBase app
Apps showcased on KhulnasoftBase can also be installed using this Docker image.

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_APPS_URL=https://khulnasoftbase.khulnasoft.com/app/2890/release/4.1.0/download
      - KHULNASOFTBASE_USERNAME=&lt;username&gt;
      - KHULNASOFTBASE_PASSWORD
      - KHULNASOFT_PASSWORD
    ports:
      - 8000:8000
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFTBASE_PASSWORD=<khulnasoftbase_password> KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create standalone with SSL enabled
To enable SSL over KhulnasoftWeb, you'll first need to generate your self-signed certificates. Please see the [Khulnasoft docs](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/Self-signcertificatesforKhulnasoftWeb) on how to go about doing this. For the purposes of local development, you can use:
```bash
openssl req -x509 -newkey rsa:4096 -passout pass:abcd1234 -keyout /home/key.pem -out /home/cert.pem -days 365 -subj /CN=localhost
```

Once you have your certificates available, you can execute the following to bring up your deployment with SSL enabled on the Khulnasoft Web UI:
```bash
$ docker run --name so1 --hostname so1 -p 8000:8000 \
              -e "KHULNASOFT_HTTP_ENABLESSL=true" \
              -e "KHULNASOFT_HTTP_ENABLESSL_CERT=/home/cert.pem" \
              -e "KHULNASOFT_HTTP_ENABLESSL_PRIVKEY=/home/key.pem" \
              -e "KHULNASOFT_HTTP_ENABLESSL_PRIVKEY_PASSWORD=abcd1234" \
              -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -v /home:/home \
              -it khulnasoft/khulnasoft:latest
```

## Create standalone with Khulnasoft Free license
[Khulnasoft Free](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/MoreaboutKhulnasoftFree) is the totally free version of Khulnasoft software. The Free license lets you index up to 500 MB per day and will never expire.

Execute the following to bring up a Khulnasoft Free standalone environment:
```bash
$ docker run --name so1 --hostname so1 -p 8000:8000 \
              -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -e "KHULNASOFT_LICENSE_URI=Free" \
              -it khulnasoft/khulnasoft:latest
```

## Create sidecar root forwarder

<details><summary markdown='span'><code>k8s-sidecar.yml</code></summary><p></p>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example
spec:
  securityContext:
    runAsUser: 0
    runAsGroup: 0
  containers:
  - name: khulnasoft-uf
    image: khulnasoft/universalforwarder:latest
    env:
    - name: KHULNASOFT_START_ARGS
      value: --accept-license
    - name: KHULNASOFT_USER
      value: root
    - name: KHULNASOFT_GROUP
      value: root
    - name: KHULNASOFT_PASSWORD
      value: helloworld
    - name: KHULNASOFT_CMD
      value: add monitor /var/log/
    - name: KHULNASOFT_STANDALONE_URL
      value: khulnasoft.company.internal
    volumeMounts:
    - name: shared-data
      mountPath: /var/log
  - name: my-app
    image: my-app
    volumeMounts:
    - name: shared-data
      mountPath: /app/logs/
  volumes:
  - name: shared-data
    emptyDir: {}
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ kubectl apply -f k8s-sidecar.yml
```

Alternatively, if you're not using Kubernetes you can use the Docker CLI to bring up the Universal Forwarder under the `root` user with the following:
```
$ docker run -d -P --user root -e KHULNASOFT_START_ARGS=--accept-license -e KHULNASOFT_PASSWORD=helloworld -e KHULNASOFT_USER=root -e KHULNASOFT_GROUP=root khulnasoft/universalforwarder:latest
```

After your pod is ready, the universal forwarder will be reading the logs generated by your app via the shared volume mount. In the ideal case, your app is generating the logs while the forwarder is reading them and streaming the output to a separate Khulnasoft instance located at khulnasoft.company.internal.

## Create standalone and universal forwarder
You can also enable distributed deployments. In this case, we can create a Khulnasoft universal forwarder running in a container to stream logs to a Khulnasoft standalone, also running in a container.

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  uf1:
    networks:
      khulnasoftnet:
        aliases:
          - uf1
    image: ${UF_IMAGE:-khulnasoft/universalforwarder:latest}
    hostname: uf1
    container_name: uf1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_STANDALONE_URL=so1
      - KHULNASOFT_ADD=udp 1514,monitor /var/log/*
      - KHULNASOFT_PASSWORD
    ports:
      - 8089

  so1:
    networks:
      khulnasoftnet:
        aliases:
          - so1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_STANDALONE_URL=so1
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
      - 8089
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create heavy forwarder
The following will allow you spin up a forwarder, and stream its logs to an independent, external indexer located at `idx1-khulnasoft.company.internal`, as long as that hostname is reachable on your network.

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  hf1:
    networks:
      khulnasoftnet:
        aliases:
          - hf1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: hf1
    container_name: hf1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_ROLE=khulnasoft_heavy_forwarder
      - KHULNASOFT_INDEXER_URL=idx1-khulnasoft.company.internal
      - KHULNASOFT_ADD=tcp 1514
      - KHULNASOFT_PASSWORD
    ports:
      - 1514
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create heavy forwarder and deployment server
The following will allow you spin up a forwarder, and stream its logs to an independent, external indexer located at `idx1-khulnasoft.company.internal`, as long as that hostname is reachable on your network. Additionally, it brings up a deployment server, which will download an app and distribute it to the heavy forwarder.

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  hf1:
    networks:
      khulnasoftnet:
        aliases:
          - hf1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: hf1
    container_name: hf1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_ROLE=khulnasoft_heavy_forwarder
      - KHULNASOFT_INDEXER_URL=idx1-khulnasoft.company.internal
      - KHULNASOFT_DEPLOYMENT_SERVER=depserver1
      - KHULNASOFT_ADD=tcp 1514
      - KHULNASOFT_PASSWORD
    ports:
      - 1514

  depserver1:
    networks:
      khulnasoftnet:
        aliases:
          - depserver1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: depserver1
    container_name: depserver1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_ROLE=khulnasoft_deployment_server
      - KHULNASOFT_APPS_URL=https://artifact.company.internal/khulnasoft_app.tgz
      - KHULNASOFT_PASSWORD
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create indexer cluster
To enable indexer cluster, we'll need to generate some common passwords and secret keys across all members of the deployment. To facilitate this, you can use the `khulnasoft/khulnasoft` image with the `create-defaults` command as so:
```
$ docker run -it -e KHULNASOFT_PASSWORD=<password> khulnasoft/khulnasoft:latest create-defaults > default.yml
```

Additionally, review the `docker-compose.yml` below to understand how linking Khulnasoft instances together through roles and environment variables is accomplished:

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
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
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_search_head
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

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
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

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
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

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
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

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
      - KHULNASOFT_SEARCH_HEAD_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

## Create search head cluster
To enable search head clustering, we'll need to generate some common passwords and secret keys across all members of the deployment. To facilitate this, you can use the `khulnasoft/khulnasoft` image with the `create-defaults` command as so:
```
$ docker run -it -e KHULNASOFT_PASSWORD=<password> khulnasoft/khulnasoft:latest create-defaults > default.yml
```

Additionally, review the `docker-compose.yml` below to understand how linking Khulnasoft instances together through roles and environment variables is accomplished:

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
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
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_ROLE=khulnasoft_search_head_captain
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  sh2:
    networks:
      khulnasoftnet:
        aliases:
          - sh2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: sh2
    container_name: sh2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  sh3:
    networks:
      khulnasoftnet:
        aliases:
          - sh3
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: sh3
    container_name: sh3
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  dep1:
    networks:
      khulnasoftnet:
        aliases:
          - dep1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: dep1
    container_name: dep1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_ROLE=khulnasoft_deployer
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  idx1:
    networks:
      khulnasoftnet:
        aliases:
          - idx1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: idx1
    container_name: idx1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ docker-compose up -d
```

## Create indexer cluster and search head cluster
To enable both clustering modes, we'll need to generate some common passwords and secret keys across all members of the deployment. To facilitate this, you can use the `khulnasoft/khulnasoft` image with the `create-defaults` command as so:
```
$ docker run -it -e KHULNASOFT_PASSWORD=<password> khulnasoft/khulnasoft:latest create-defaults > default.yml
```

Additionally, review the `docker-compose.yml` below to understand how linking Khulnasoft instances together through roles and environment variables is accomplished:

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
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
    hostname: sh1
    container_name: sh1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_search_head_captain
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  sh2:
    networks:
      khulnasoftnet:
        aliases:
          - sh2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: sh2
    container_name: sh2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  sh3:
    networks:
      khulnasoftnet:
        aliases:
          - sh3
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: sh3
    container_name: sh3
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_search_head
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  dep1:
    networks:
      khulnasoftnet:
        aliases:
          - dep1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: dep1
    container_name: dep1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_deployer
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  cm1:
    networks:
      khulnasoftnet:
        aliases:
          - cm1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: cm1
    container_name: cm1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_cluster_master
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  idx1:
    networks:
      khulnasoftnet:
        aliases:
          - idx1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: idx1
    container_name: idx1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  idx2:
    networks:
      khulnasoftnet:
        aliases:
          - idx2
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: idx2
    container_name: idx2
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml

  idx3:
    networks:
      khulnasoftnet:
        aliases:
          - idx3
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: idx3
    container_name: idx3
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_INDEXER_URL=idx1,idx2,idx3
      - KHULNASOFT_SEARCH_HEAD_URL=sh2,sh3
      - KHULNASOFT_SEARCH_HEAD_CAPTAIN_URL=sh1
      - KHULNASOFT_CLUSTER_MASTER_URL=cm1
      - KHULNASOFT_ROLE=khulnasoft_indexer
      - KHULNASOFT_DEPLOYER_URL=dep1
    ports:
      - 8000
      - 8089
    volumes:
      - ./default.yml:/tmp/defaults/default.yml
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ docker-compose up -d
```

## Enable root endpoint on KhulnasoftWeb

<details><summary markdown='span'><code>docker-compose.yml</code></summary><p></p>

```yaml
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_ROOT_ENDPOINT=/khulnasoftweb
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
```
</details><p></p>

Execute the following to bring up your deployment:
```
$ KHULNASOFT_PASSWORD=<password> docker-compose up -d
```

Then, visit KhulnasoftWeb on your browser with the root endpoint in the URL, such as `http://localhost:8000/khulnasoftweb`.

## More
There are a variety of Docker compose scenarios in the `docker-khulnasoft` repo [here](https://github.com/khulnasoft/docker-khulnasoft/tree/develop/test_scenarios). Feel free to use any of those for reference in deploying different topologies!
