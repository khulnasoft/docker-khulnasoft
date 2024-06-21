## Installing a Khulnasoft Enterprise License
The Khulnasoft Docker image supports the ability to bring your own Enterprise license. By default, the image includes the ability to use up to the trial license. Please see the documentation for more information on what [additional features and capabilities are unlocked with a full Enterprise license](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/HowKhulnasoftlicensingworks)

There are primarily two different ways to apply a license when starting your container: either through a file/directory volume-mounted inside the container, or through an external URL for dynamic downloads. The environment variable `KHULNASOFT_LICENSE_URI` supports both of these methods.


## Navigation

* [Path to file](#path-to-file)
* [Download via URL](#download-via-url)
* [Free license](#khulnasoft-free-license)
* [Using a license master](#using-a-license-master)
* [Using a remote instance](#using-a-remote-instance)

## Path to file
We recommend using [Docker Secrets](https://docs.docker.com/engine/swarm/secrets) to manage your license. However, in a development environment, you can also specify a volume-mounted path to a file.

If you plan on using secrets storage, the initial step must be to create that secret. In the case of using Docker, you can run:
```
$ docker secret create khulnasoft_license path/to/khulnasoft.lic
```

Please refer to these separate docker-compose.yml files for how to use secrets or direct volume mounts:
<details><summary>docker-compose.yml - with secret</summary><p>

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_LICENSE_URI=/run/secrets/khulnasoft_license
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
    secrets:
      - khulnasoft_license
secrets:
    khulnasoft_license:
        external: true
```
</p></details>

<details><summary>docker-compose.yml - with volume mount</summary><p>

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_LICENSE_URI=/tmp/khulnasoft.lic
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
    volumes:
      - ./khulnasoft.lic:/tmp/khulnasoft.lic
```
</p></details>

You should be able to bring up your deployment with the Khulnasoft license automatically applied with the following command:
```
$ KHULNASOFT_PASSWORD=<password> docker stack deploy --compose-file=docker-compose.yml khulnasoft_deployment
```

## Download via URL
If you plan on hosting your license on a reachable file server, you can dynamically fetch and download your license from the container. This can be an easy way use a license without pre-seeding your container's environment runtime with various secrets/files.

Please refer to the following compose file for how to use a URL:
<details><summary>docker-compose.yml - with URL</summary><p>

```
version: "3.6"

services:
  so1:
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    hostname: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_LICENSE_URI=http://webserver/path/to/khulnasoft.lic
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
```
</p></details>

You should be able to bring up your deployment with the Khulnasoft license automatically applied with the following command:
```
$ KHULNASOFT_PASSWORD=<password> docker stack deploy --compose-file=docker-compose.yml khulnasoft_deployment
```

## Khulnasoft Free license
Not to be confused with an actual free Khulnasoft enterprise license, but [Khulnasoft Free](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/MoreaboutKhulnasoftFree) is a product offering that enables the power of Khulnasoft with a never-expiring but ingest-limited license. By default, when you create a Khulnasoft environment using this Docker container, it will enable a Khulnasoft Trial license which is good for 30 days from the start of your instance. With Khulnasoft Free, you can create a full developer environment of Khulnasoft for any personal, sustained usage.

To bring up a single instance using Khulnasoft Free, you can run the following command:
```
$ docker run --name so1 --hostname so1 -p 8000:8000 -e KHULNASOFT_PASSWORD=<password> -e KHULNASOFT_START_ARGS=--accept-license -e KHULNASOFT_LICENSE_URI=Free -it khulnasoft/khulnasoft:latest
```

## Using a license master
When starting up a distributed Khulnasoft deployment, it may be inefficient for each Khulnasoft instance to apply/fetch the same license. Luckily, there is a dedicated Khulnasoft role for this - `khulnasoft_license_master`. For more information on what this role is, please refer to Khulnasoft documentation on [license masters](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Configurealicensemaster).

Please refer to the following compose file for how to bring up a license master:
<details><summary>docker-compose.yml - license master</summary><p>

```
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
  lm1:
    networks:
      khulnasoftnet:
        aliases:
          - lm1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: lm1
    container_name: lm1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_STANDALONE_URL=so1
      - KHULNASOFT_LICENSE_MASTER_URL=lm1
      - KHULNASOFT_ROLE=khulnasoft_license_master
      - KHULNASOFT_LICENSE_URI=http://webserver/path/to/khulnasoft.lic
      - KHULNASOFT_PASSWORD

  so1:
    networks:
      khulnasoftnet:
        aliases:
          - so1
    image: ${KHULNASOFT_IMAGE:-khulnasoft/khulnasoft:latest}
    command: start
    hostname: so1
    container_name: so1
    environment:
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_STANDALONE_URL=so1
      - KHULNASOFT_LICENSE_MASTER_URL=lm1
      - KHULNASOFT_ROLE=khulnasoft_standalone
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
```
</p></details>

Note that in the above, only the license master container `lm1` needs to download and apply the license. When the standalone `so1` container comes up, it will detect (based off the environment variable `KHULNASOFT_LICENSE_MASTER_URL`) that there is a central license master, and consequently add itself as a license slave to that host.

## Using a remote instance
Alternatively, you may elect to create your Khulnasoft environment all within containers but host the license master externally such that it can be used by multiple teams or organizations. These images support this type of configuration, through the following example:
```yaml
version: "3.6"

networks:
  khulnasoftnet:
    driver: bridge
    attachable: true

services:
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
      - KHULNASOFT_LICENSE_MASTER_URL=http://central-license-master.internal.com:8088
      - KHULNASOFT_ROLE=khulnasoft_standalone
      - KHULNASOFT_PASSWORD
    ports:
      - 8000
```

Note that it's possible to use a different protocol and port when supplying the license master URL. If scheme and port are not provided, the playbooks fall back to using `https` and the `8089` Khulnasoft Enterprise management port.
