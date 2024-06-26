## Advanced

Let's dive into the nitty-gritty of how to tweak the setup of your containerized Khulnasoft deployment. This section goes over in detail various features and functionality that a traditional Khulnasoft Enterprise solution is capable of.

## Navigation

* [Runtime configuration](#runtime-configuration)
    * [Using `default.yml`](#using-defaultyml)
    * [Configuration specs for `default.yml`](#configuration-specs-for-defaultyml)
        * [Global variables](#global-variables)
        * [Configure Khulnasoft](#configure-khulnasoft)
        * [Configured app installation paths](#configure-app-installation-paths)
        * [Configure search head clustering](#configure-search-head-clustering)
        * [Configure indexer clustering](#configure-indexer-clustering)
* [Install apps](#install-apps)
* [Apply Khulnasoft license](#apply-khulnasoft-license)
* [Create custom configs](#create-custom-configs)
* [Enable SmartStore](#enable-smartstore)
    * [Configure cache manager](#configure-cache-manager)
* [Forward to Data Stream Processor](#forward-to-data-stream-processor)
* [Use a deployment server](#use-a-deployment-server)
* [Deploy distributed topology](#deploy-distributed-topology)
* [Enable SSL internal communication](#enable-ssl-internal-communication)
* [Build from source](#build-from-source)
    * [Supported platforms](#supported-platforms)
    * [Base image](#base-image)
    * [Khulnasoft image](#khulnasoft-image)
    * [Universal Forwarder Image](#universal-forwarder-image)

----

## Runtime configuration
The Khulnasoft Docker image has several functions that can be configured by either supplying a `default.yml` file or by passing in environment variables. These configurations are consumed by an inventory script in the [khulnasoft-ansible project](https://github.com/khulnasoft/khulnasoft-ansible).

[Supported environment variables](https://khulnasoft.github.io/khulnasoft-ansible/ADVANCED.html#inventory-script) can be found in the khulnasoft-ansible documentation.

### Using default.yml
The purpose of the `default.yml` is to define a standard set of variables that controls how Khulnasoft gets set up. This is particularly important when deploying clustered Khulnasoft topologies, as there are frequent variables that you need to be consistent across all members of the cluster (ex. keys, passwords, secrets).

#### Generation
The image contains a script to enable dynamic generation of this file automatically. Run the following command to generate a `default.yml`:
```bash
$ docker run --rm -it khulnasoft/khulnasoft:latest create-defaults > default.yml
```

You can also pre-seed some settings based on environment variables during this `default.yml` generation process. For example, you can define `KHULNASOFT_PASSWORD` with the following command:
```bash
$ docker run --rm -it -e KHULNASOFT_PASSWORD=<password> khulnasoft/khulnasoft:latest create-defaults > default.yml
```
#### Usage
When starting the docker container, the `default.yml` can be mounted in `/tmp/defaults/default.yml` or fetched dynamically with `KHULNASOFT_DEFAULTS_URL`. Ansible provisioning will read in and honor these settings.

Environment variables specified at runtime will take precedence over anything defined in `default.yml`.
```bash
# Volume-mounting option using --volumes/-v flag
$ docker run -d -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" \
             -e "KHULNASOFT_START_ARGS=--accept-license" \
             -v "$(pwd)/default.yml:/tmp/defaults/default.yml" \
             khulnasoft/khulnasoft:latest

# Volume-mounting option using --mount flag
$ docker run -d -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" \
             -e "KHULNASOFT_START_ARGS=--accept-license" \
             --mount type=bind,source="$(pwd)"/default.yml,target=/tmp/defaults/default.yml
             khulnasoft/khulnasoft:latest

# URL option
$ docker run -d -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" \
             -e "KHULNASOFT_START_ARGS=--accept-license" \
             -e "KHULNASOFT_DEFAULTS_URL=http://company.net/path/to/default.yml" \
             khulnasoft/khulnasoft:latest
```

Additionally, note that you do not need to supply the full `default.yml` if you only choose to modify a portion of how Khulnasoft Enterprise is configured upon boot. For instance, if you wish to take advantage of the ability to write conf files through the `khulnasoft.conf` key, the full `default.yml` passed in will simply look like the following:
```
khulnasoft:
  conf:
    - key: indexes
      value:
        directory: /opt/khulnasoft/etc/system/local
        content:
          test:
            homePath: $KHULNASOFT_DB/test/db
            coldPath: $KHULNASOFT_DB/test/colddb
            thawedPath: $KHULNASOFT_DB/test/thaweddb
```

### Configuration specs for default.yml

#### Global variables

Variables at the root level influence the behavior of everything in the container, as they have global scope.

Example:
```yaml
---
retry_num: 100
```

| Variable Name | Description | Parent Object | Default Value | Required for Standalone | Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- | --- | --- |
| retry_num | Default number of loop attempts to connect containers | none | 100 | yes | yes | yes |

#### Configure Khulnasoft

The major object `khulnasoft` in the YAML file contains variables that control how Khulnasoft operates.

Sample:
<!-- {% raw %} -->
```yaml
---
khulnasoft:
  opt: /opt
  home: /opt/khulnasoft
  user: khulnasoft
  group: khulnasoft
  exec: /opt/khulnasoft/bin/khulnasoft
  pid: /opt/khulnasoft/var/run/khulnasoft/khulnasoftd.pid
  password: "{{ khulnasoft_password | default(<password>) }}"
  svc_port: 8089
  s2s_port: 9997
  http_port: 8000
  hec:
    enable: True
    ssl: True
    port: 8088
    # hec.token is used only for ingestion (receiving Khulnasoft events)
    token: <default_hec_token>
  smartstore: null
  ...
```
<!-- {% endraw %} -->

| Variable Name | Description | Parent Object | Default Value | Required for Standalone | Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- | --- | --- |
| opt | Parent directory where Khulnasoft is running | khulnasoft | /opt | yes | yes | yes |
| home | Location of the Khulnasoft Installation | khulnasoft | /opt/khulnasoft | yes | yes | yes |
| user | Operating System User to Run Khulnasoft Enterprise As | khulnasoft | khulnasoft | yes | yes | yes |
| group | Operating System Group to Run Khulnasoft Enterprise As | khulnasoft | khulnasoft | yes | yes | yes |
| exec | Path to the Khulnasoft Binary | khulnasoft | /opt/khulnasoft/bin/khulnasoft | yes | yes | yes |
| pid | Location to the Running PID File | khulnasoft | /opt/khulnasoft/var/run/khulnasoft/khulnasoftd.pid | yes | yes | yes
| root_endpoint | Set root endpoint for KhulnasoftWeb (for reverse proxy usage) | khulnasoft | **none** | no | no | no |
| password | Password for the admin account | khulnasoft | **none** | yes | yes | yes |
| svc_port | Default Admin Port | khulnasoft | 8089 | yes | yes | yes |
| s2s_port | Default Forwarding Port | khulnasoft | 9997 | yes | yes | yes |
| http_port | Default KhulnasoftWeb Port | khulnasoft | 8000 | yes | yes | yes |
| hec.enable | Enable / Disable HEC | khulnasoft | True | no | no | no |
| hec.ssl | Force HEC to use encryption | khulnasoft | True | no | no | no |
| hec.port | Default HEC Input Port | khulnasoft | 8088 | no | no | no |
| hec.token | Token to enable for HEC inputs | khulnasoft | **none** | no | no | no |
| smartstore | Configuration params for [SmartStore](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Indexer/AboutSmartStore) bootstrapping | khulnasoft | null | no | no | no |

#### Configure app installation paths

The `app_paths` section under `khulnasoft` controls how apps are installed inside the container.

Sample:
```yaml
---
khulnasoft:
  app_paths:
    default: /opt/khulnasoft/etc/apps
    shc: /opt/khulnasoft/etc/shcluster/apps
    idxc: /opt/khulnasoft/etc/master-apps
    httpinput: /opt/khulnasoft/etc/apps/khulnasoft_httpinput
  ...
```

| Variable Name | Description | Parent Object | Default Value | Required for Standalone | Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- | --- | --- |
| default | Normal apps for standalone instances will be installed in this location | khulnasoft.app_paths | **none** | no | no | no |
| shc | Apps for search head cluster instances will be installed in this location (usually only done on the deployer)| khulnasoft.app_paths | **none** | no | no | no |
| idxc | Apps for index cluster instances will be installed in this location (usually only done on the cluster master)| khulnasoft.app_paths | **none** | no | no | no |
| httpinput | App to use and configure when setting up HEC based instances.| khulnasoft.app_paths | **none** | no | no | no |

#### Configure search head clustering

Search Head Clustering is configured using the `shc` section under `khulnasoft`.

Sample:
```yaml
---
khulnasoft:
  shc:
    enable: false
    secret: <secret_key>
    replication_factor: 3
    replication_port: 9887
  ...
```

| Variable Name | Description | Parent Object | Default Value | Required for Standalone | Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- | --- | --- |
| enable | Instructs the container to create a search head cluster | khulnasoft.shc | false | no | yes | no |
| secret | A secret phrase to use for all SHC communication and binding. Once set, this cannot be changed without rebuilding the cluster. | khulnasoft.shc | **none** | no | yes | no |
| replication_factor | Consult [the docs](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/DistSearch/ChooseSHCreplicationfactor) for valid settings for your use case | khulnasoft.shc | 3 | no | yes | no |
| replication_port | Default port for the SHC to communicate on | khulnasoft.shc | 9887 | no | yes | no |

#### Configure indexer clustering

Indexer Clustering is configured using the `idxc` section under `khulnasoft`.

Sample:
```yaml
---
khulnasoft:
  idxc:
    secret: <secret_key>
    search_factor: 2
    replication_factor: 3
    replication_port: 9887
  ...
```

| Variable Name | Description | Parent Object | Default Value | Required for Standalone| Required for Search Head Clustering | Required for Index Clustering |
| --- | --- | --- | --- | --- | --- | --- |
| secret | Secret used for transmission between the cluster master and indexers | khulnasoft.idxc | **none** | no | no | yes |
| search_factor | Search factor to be used for search artifacts | khulnasoft.idxc | 2 | no | no | yes |
| replication_factor | Bucket replication factor used between index peers | khulnasoft.idxc | 3 | no | no | yes |
| replication_port | Bucket replication Port between index peers | khulnasoft.idxc | 9887 | no | no | yes |

## Install apps
Apps can be installed by using the `KHULNASOFT_APPS_URL` environment variable when creating the Khulnasoft container:
```bash
$ docker run --name khulnasoft -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -e "KHULNASOFT_APPS_URL=http://company.com/path/to/app.tgz" \
              -it khulnasoft/khulnasoft:latest
```

See the [full app installation guide](advanced/APP_INSTALL.md) to learn how to specify multiple apps and how to install apps in a distributed environment.

## Apply Khulnasoft license
Licenses can be added with the `KHULNASOFT_LICENSE_URI` environment variable when creating the Khulnasoft container:
```bash
$ docker run --name khulnasoft -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -e "KHULNASOFT_LICENSE_URI=http://company.com/path/to/khulnasoft.lic" \
              -it khulnasoft/khulnasoft:latest
```

See the [full license installation guide](advanced/LICENSE_INSTALL.md) to learn how to specify multiple licenses and how to use a central, containerized license manager.

## Create custom configs
When Khulnasoft boots, it registers all the config files in various locations on the filesystem under `${KHULNASOFT_HOME}`. These are settings that control how Khulnasoft operates. See [About configuration files](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles) for more information.

Using the Khulnasoft Docker image, users can also create their own config files, following the same INI file format that drives Khulnasoft. This is a power-user/admin-level feature, as invalid config files can break or prevent start-up of your Khulnasoft installation.

User-specified config files are set in `default.yml` by creating a `conf` key under `khulnasoft`, in the format below:
```yaml
---
khulnasoft:
  conf:
    - key: user-prefs
      value:
        directory: /opt/khulnasoftforwarder/etc/users/admin/user-prefs/local
        content:
          general:
            default_namespace: appboilerplate
            search_syntax_highlighting: dark
  ...
```

**NOTE:** Previously, the `khulnasoft.conf` entry supported a dictionary mapping. Both types will continue to work, but it is highly recommended you move to the new array-based type, as this will become the standard.

This generates a file `user-prefs.conf`, owned by the correct Khulnasoft user and group and located in the given directory (in this case, `/opt/khulnasoftforwarder/etc/users/admin/user-prefs/local`).

Following INI format, the contents of `user-prefs.conf` will resemble the following:
```ini
[general]
search_syntax_highlighting = dark
default_namespace = appboilerplate
```

For multiple custom configuration files, add more entries under the `conf` key of `default.yml`.

**CAUTION:** Using this method of configuration file generation may not create a configuration file the way Khulnasoft expects. Verify the generated configuration file to avoid errors. Use at your own discretion.

## Enable SmartStore
SmartStore utilizes S3-compliant object storage to store indexed data.

This is a capability only available for indexer clusters (cluster_master + indexers). Learn more [About SmartStore](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Indexer/AboutSmartStore) and [Decoupling compute and storage](https://www.khulnasoft.com/blog/2018/10/11/khulnasoft-smartstore-cut-the-cord-by-decoupling-compute-and-storage.html) from Khulnasoft documentation and blog posts.

The Khulnasoft Docker image supports SmartStore in a bring-your-own backend storage provider format. Due to the complexity of this option, SmartStore is only enabled if you specify all the parameters in your `default.yml` file.

Sample configuration that persists *all* indexes (default) with a SmartStore backend:
```yaml
---
khulnasoft:
  smartstore:
    index:
      - indexName: default
        remoteName: remote_store
        scheme: s3
        remoteLocation: <bucket-name>
        s3:
          access_key: <access_key>
          secret_key: <secret_key>
          endpoint: http://s3-us-west-2.amazonaws.com
  ...
```

### Configure cache manager

The SmartStore cache manager controls data movement between the indexer and the remote storage tier. It is configured here in parallel with `server.conf` and `indexes.conf` options:

* The `cachemanager` stanza corresponds to `[cachemanager]` in the [server.conf options](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/admin/Serverconf).
* The `index` stanza corresponds to [indexes.conf options](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/admin/Indexesconf).

This example defines cache settings and retention policy:
```yaml
khulnasoft:
  smartstore:
    cachemanager:
      max_cache_size: 500
      max_concurrent_uploads: 7
    index:
      - indexName: custom_index
        remoteName: my_storage
        scheme: http
        remoteLocation: my_storage.net
        maxGlobalDataSizeMB: 500
        maxGlobalRawDataSizeMB: 200
        hotlist_recency_secs: 30
        hotlist_bloom_filter_recency_hours: 1
  ...
```

## Forward to Data Stream Processor
See the [DSP integration document](advanced/DSP.md) to learn how to directly send data from a forwarder to [Khulnasoft Data Stream Processor](https://www.khulnasoft.com/en_us/software/stream-processing.html).

## Use a deployment server
Deployment servers can be used to manage otherwise unclustered or disjoint Khulnasoft instances. A primary use-case would be to stand up a deployment server to manage app or configuration distribution to a fleet of 100 universal forwarders.

See the [full deployment server guide](advanced/DEPLOYMENT_SERVER.md) to understand how you can leverage this role in your topology.

## Deploy distributed topology
While a standalone Khulnasoft instance may be fine for testing and development, you may eventually want to enable better performance by running Khulnasoft at scale. The Khulnasoft Docker image supports a fully-vetted distributed Khulnasoft environment, networking everything together and using environment variables that enable specific containers to assume specified roles.

See [Starting a Khulnasoft cluster](advanced/DISTRIBUTED_TOPOLOGY.md) to learn how to set up a distributed, containerized environment.

## Enable SSL Internal Communication
To secure network traffic from one Khulnasoft instance to another (e.g. forwarders to indexers), you can enable forwarding and receiving to use SSL certificates.

If you are enabling SSL on one tier of your Khulnasoft topology, it's likely all instances will need it. To achieve this, generate your server and CA certificates and add them to the `default.yml`, which gets shared across all Khulnasoft docker containers.

Sample `default.yml` snippet to configure Khulnasoft TCP with SSL:
```yaml
khulnasoft:
  ...
  s2s:
    ca: /mnt/certs/ca.pem
    cert: /mnt/certs/cert.pem
    enable: true
    password: abcd1234
    port: 9997
    ssl: true
  ...
```

Fore further instructions, see [Configure Khulnasoft forwarding to use your own certificates](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates).

## Build from source
Building your own images from source is possible, but neither supported nor recommended.It can be useful for incorporating very experimental features, testing new features, or using your own registry for persistent images.

The supplied `Makefile` in the root of this project contains commands to control the build:
1. Fork the [docker-khulnasoft GitHub repository](https://github.com/khulnasoft/docker-khulnasoft/)
1. Clone your fork using git and create a branch off develop
    ```bash
    $ git clone git@github.com:YOUR_GITHUB_USERNAME/docker-khulnasoft.git
    $ cd docker-khulnasoft
    ```
1. Use the appropriate `make` targets to build your images
    ```
    $ make khulnasoft-redhat-8
    $ make uf-redhat-8
    ```
1. Run the corresponding tests to verify your environment
    ```
    $ make test_redhat8
    ```

### Supported platforms

| Platform  | Image Suffix |
| --------- | ------------ |
| Red Hat 8 | `-redhat-8`  |
| Debian 9  | `-debian-9`  |
| Debian 10 | `-debian-10` |
| CentOS 7  | `-centos-7`  |

### Base image
The `base/` directory contains Dockerfiles for base platform images on top of which all other images are built.
```
$ make base-redhat-8
```
**WARNING:** Modifications made to the "base" image can result in Khulnasoft being unable to start or run correctly.

### Khulnasoft image
The `khulnasoft/common-files` directory contains a Dockerfile that extends the base image by installing Khulnasoft and adding tools for provisioning. Advanced Khulnasoft provisioning capabilities are provided by an entrypoint script and playbooks published separately, via the [khulnasoft-ansible project](https://github.com/khulnasoft/khulnasoft-ansible).

  * **Minimal image**

    Build a stripped-down Khulnasoft base image with many files excluded. This is primarily intended for experimental use.
    ```
    $ make minimal-redhat-8
    ```
  * **Bare image**

    Build a full Khulnasoft base image *without* Ansible.
    ```
    $ make bare-redhat-8
    ```
  * **Full image**

    Build a full Khulnasoft base image *with* Ansible.
    ```
    $ make khulnasoft-redhat-8
    ```

### Universal Forwarder image
The `uf/common-files` directory contains a Dockerfile that extends the base image by installing Khulnasoft Universal Forwarder and adding tools for provisioning. This image is similar to the Khulnasoft Enterprise image (`khulnasoft-redhat-8`), except the more lightweight Khulnasoft Universal Forwarder package is installed instead.
```
$ make uf-redhat-8
```
