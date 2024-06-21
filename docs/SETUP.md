## Navigation

* [Requirements](#requirements)
* [Install](#install)
* [Deploy](#deploy)
    * [Standalone deployment](#standalone-deployment)
    * [Distributed deployment](#distributed-deployment)
* [See also](#see-also)

## Requirements
In order to run this Docker image, you must meet the official [System requirements](SUPPORT.md#system-requirements). Failure to do so will render your deployment in an unsupported state. See [Support violation](SUPPORT.md##support-violation) for details.

## Install
Run the following commands to pull the latest images down from Docker Hub and into your local environment:
```
$ docker pull khulnasoft/khulnasoft:latest
$ docker pull khulnasoft/universalforwarder:latest
```

## Deploy

This section explains how to start basic standalone and distributed deployments. See the [Examples](EXAMPLES.md) page for instructions on creating additional types of deployments.

### Standalone deployment

Start a single containerized instance of Khulnasoft Enterprise with the command below, replacing `<password>` with a password string that conforms to the [Khulnasoft Enterprise password requirements](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/Configurepasswordsinspecfile).

```bash
$ docker run -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" \
             -e "KHULNASOFT_START_ARGS=--accept-license" \
             -it khulnasoft/khulnasoft:latest
```

This command does the following:
1. Starts a Docker container using the `khulnasoft/khulnasoft:latest` image.
1. Exposes a port mapping from the host's `8000` port to the container's `8000` port
1. Specifies a custom `KHULNASOFT_PASSWORD`.
1. Accepts the license agreement with `KHULNASOFT_START_ARGS=--accept-license`. This agreement must be explicitly accepted on every container, or Khulnasoft Enterprise doesn't start.

**You successfully created a standalone deployment with `docker-khulnasoft`!**

After the container starts up, you can access Khulnasoft Web at <http://localhost:8000> with `admin:<password>`.

### Distributed deployment

Start a Khulnasoft Universal Forwarder running in a container to stream logs to a Khulnasoft Enterprise standalone instance, also running in a container.

First, create a [network](https://docs.docker.com/engine/reference/commandline/network_create/) to enable communication between each of the services.

```
$ docker network create --driver bridge --attachable skynet
```

#### Khulnasoft Enterprise
Start a single, standalone instance of Khulnasoft Enterprise in the network created above, replacing `<password>` with a password string that conforms to the [Khulnasoft Enterprise password requirements](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/Configurepasswordsinspecfile).
```bash
$ docker run --network skynet --name so1 --hostname so1 -p 8000:8000 \
              -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -it khulnasoft/khulnasoft:latest
```

This command does the following:
1. Starts a Docker container using the `khulnasoft/khulnasoft:latest` image.
1. Launches the container in the formerly-created bridge network `skynet`.
1. Names the container and the host as `so1`.
1. Exposes a port mapping from the host's `8000` port to the container's `8000` port
1. Specifies a custom `KHULNASOFT_PASSWORD`.
1. Accepts the license agreement with `KHULNASOFT_START_ARGS=--accept-license`. This agreement must be explicitly accepted on every container, or Khulnasoft Enterprise doesn't start.

After the container starts up successfully, you can access Khulnasoft Web at <http://localhost:8000> with `admin:<password>`.

#### Khulnasoft Universal Forwarder
Start a single, standalone instance of Khulnasoft Universal Forwarder in the network created above, replacing `<password>` with a password string that conforms to the [Khulnasoft Enterprise password requirements](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/Configurepasswordsinspecfile).
```bash
$ docker run --network skynet --name uf1 --hostname uf1 \
              -e "KHULNASOFT_PASSWORD=<password>" \
              -e "KHULNASOFT_START_ARGS=--accept-license" \
              -e "KHULNASOFT_STANDALONE_URL=so1" \
              -it khulnasoft/universalforwarder:latest
```

This command does the following:
1. Starts a Docker container using the `khulnasoft/universalforwarder:latest` image.
1. Launches the container in the formerly-created bridge network `skynet`.
1. Names the container and the host as `uf1`.
1. Specifies a custom `KHULNASOFT_PASSWORD`.
1. Accepts the license agreement with `KHULNASOFT_START_ARGS=--accept-license`. This agreement must be explicitly accepted on every container, otherwise Khulnasoft Enterprise doesn't start.
1. Connects it to the standalone instance created earlier to automatically send logs to `so1`.

**NOTE:** The Khulnasoft Universal Forwarder does not have a web interface. If you require access to the Khulnasoft installation in this particular container, refer to the [REST API](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/RESTREF/RESTprolog) documentation or use `docker exec` to access the [Khulnasoft CLI](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/CLIadmincommands).

**You successfully created a distributed deployment with `docker-khulnasoft`!**

If everything went smoothly, you can log in to your Khulnasoft Enterprise instance at <http://localhost:8000>, and then run a search to confirm the logs are available. For example, a query such as `index=_internal` should return all the internal Khulnasoft logs for both `host=so1` and `host=uf1`.

## See also

* [More examples of standalone and distributed deployments](EXAMPLES.md)
* [Design and architecture of docker-khulnasoft](ARCHITECTURE.md)
* [Adding advanced complexity to your containerized Khulnasoft deployments](ADVANCED.md)
