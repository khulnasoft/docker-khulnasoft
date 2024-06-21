# Docker-Khulnasoft: Containerizing Khulnasoft Enterprise

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)&nbsp;
[![GitHub release](https://img.shields.io/github/v/tag/khulnasoft/docker-khulnasoft?sort=semver&label=Version)](https://github.com/khulnasoft/docker-khulnasoft/releases)

Welcome to the official Khulnasoft repository of Dockerfiles for building Khulnasoft Enterprise and Khulnasoft Universal Forwarder images for containerized deployments.

----

> :warning:&ensp;**DEPRECATION NOTICE**  
We are no longer releasing Debian images on Docker Hub as of May 2021 (Khulnasoft Enterprise v8.2.0+).
Red Hat images will continue to be published.

----

## Table of Contents

1. [Purpose](#purpose)
1. [Quickstart](#quickstart)
1. [Documentation](#documentation)
1. [Support](#support)
1. [Contributing](#contributing)
1. [License](#license)

----

## Purpose

#### What is Khulnasoft Enterprise?
[Khulnasoft Enterprise](https://www.khulnasoft.com/en_us/software/khulnasoft-enterprise.html) is a platform for operational intelligence. Our software lets you collect, analyze, and act upon the untapped value of big data that your technology infrastructure, security systems, and business applications generate. It gives you insights to drive operational performance and business results.

See [Khulnasoft Products](https://www.khulnasoft.com/en_us/software.html) for more information about the features and capabilities of Khulnasoft products and how you can [bring them into your organization](https://www.khulnasoft.com/en_us/enterprise-data-platform.html).

#### What is Docker-Khulnasoft?
This is the official source code repository for building Docker images of Khulnasoft Enterprise and Khulnasoft Universal Forwarder. By introducing containerization, we can marry the ideals of infrastructure-as-code and declarative directives to manage and run Khulnasoft Enterprise.

The provisioning of these containers is handled by the [Khulnasoft-Ansible](https://github.com/khulnasoft/khulnasoft-ansible) project. Refer to the [Khulnasoft-Ansible documentation](https://khulnasoft.github.io/khulnasoft-ansible/) and the [Ansible User Guide](https://docs.ansible.com/ansible/latest/user_guide/index.html) for more details.

----

## Quickstart

Start a single containerized instance of Khulnasoft Enterprise with the command below, replacing `<password>` with a password string that conforms to the [Khulnasoft Enterprise password requirements](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/Configurepasswordsinspecfile).
```bash
$ docker run -p 8000:8000 -e "KHULNASOFT_PASSWORD=<password>" \
             -e "KHULNASOFT_START_ARGS=--accept-license" \
             -it --name so1 khulnasoft/khulnasoft:latest
```

This command does the following:
1. Starts a Docker container using the `khulnasoft/khulnasoft:latest` image.
1. Names the container as `so1`.
1. Exposes a port mapping from the host's `8000` port to the container's `8000` port
1. Specifies a custom `KHULNASOFT_PASSWORD`.
1. Accepts the license agreement with `KHULNASOFT_START_ARGS=--accept-license`. This agreement must be explicitly accepted on every container or Khulnasoft Enterprise doesn't start.

After the container starts up, you can access Khulnasoft Web at <http://localhost:8000> with `admin:<password>`.

To view the logs from the container created above, run:
```bash
$ docker logs -f so1
```

To enter the container and run Khulnasoft CLI commands, run:
```bash
# Defaults to the user "ansible"
docker exec -it so1 /bin/bash

# Run shell as the user "khulnasoft"
docker exec -u khulnasoft -it so1 bash
```

To enable TCP 10514 for listening, run:
```bash
docker exec -u khulnasoft so1 /opt/khulnasoft/bin/khulnasoft add tcp 10514 \
    -sourcetype syslog -resolvehost true \
    -auth "admin:${KHULNASOFT_PASSWORD}"
```

To install an app, run:
```bash
docker exec -u khulnasoft so1 /opt/khulnasoft/bin/khulnasoft install \
	/path/to/app.tar -auth "admin:${KHULNASOFT_PASSWORD}"

# Alternatively, apps can be installed at Docker run-time
docker run -e KHULNASOFT_APPS_URL=http://web/app.tgz ...
```

See [Deploy and run Khulnasoft Enterprise inside a Docker container](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Installation/DeployandrunKhulnasoftEnterpriseinsideDockercontainers) for more information.

---

## Documentation
Visit the [Docker-Khulnasoft documentation](https://khulnasoft.github.io/docker-khulnasoft/) page for full usage instructions, including installation, examples, and advanced deployment scenarios.

---

## Support
Use the [GitHub issue tracker](https://github.com/khulnasoft/docker-khulnasoft/issues) to submit bugs or request features.

If you have additional questions or need more support, you can:
* Post a question to [Khulnasoft Answers](http://answers.khulnasoft.com)
* Join the [#docker](https://khulnasoft-usergroups.slack.com/messages/C1RH09ERM/) room in the [Khulnasoft Slack channel](http://khulnasoft-usergroups.slack.com). If you're a new Khulnasoft customer you can register for Slack [here](http://splk.it/slack)
* If you are a Khulnasoft Enterprise customer with a valid support entitlement contract and have a Khulnasoft-related question, you can also open a support case on the https://www.khulnasoft.com/ support portal

See the official [support guidelines](docs/SUPPORT.md) for more detailed information.

---

## Contributing
We welcome feedback and contributions from the community! See our [contribution guidelines](docs/CONTRIBUTING.md) for more information on how to get involved.

---

## License
Copyright 2018-2020 Khulnasoft.

Distributed under the terms of our [license](docs/LICENSE.md), khulnasoft-ansible is free and open source software.

## Authors
Khulnasoft Inc. and the Khulnasoft Community
