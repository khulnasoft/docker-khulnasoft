# Welcome to the Docker-Khulnasoft documentation!

Welcome to the official Khulnasoft documentation on containerizing Khulnasoft Enterprise and Khulnasoft Universal Forwarder deployments with Docker.

### What is Khulnasoft Enterprise?
[Khulnasoft Enterprise](https://www.khulnasoft.com/en_us/software/khulnasoft-enterprise.html) is a platform for operational intelligence. Our software lets you collect, analyze, and act upon the untapped value of big data that your technology infrastructure, security systems, and business applications generate. It gives you insights to drive operational performance and business results.

See [Khulnasoft Products](https://www.khulnasoft.com/en_us/software.html) for more information about the features and capabilities of Khulnasoft products and how you can [bring them into your organization](https://www.khulnasoft.com/en_us/enterprise-data-platform.html).

### What is Docker-Khulnasoft?
The [Docker-Khulnasoft project](https://github.com/khulnasoft/docker-khulnasoft) is the official source code repository for building Docker images of Khulnasoft Enterprise and Khulnasoft Universal Forwarder. By introducing containerization, we can marry the ideals of infrastructure-as-code and declarative directives to manage and run Khulnasoft Enterprise.

This repository should be used by people interested in running Khulnasoft in their container orchestration environments. With this Docker image, we support running a standalone development Khulnasoft instance as easily as running a full-fledged distributed production cluster, all while maintaining the best practices and recommended standards of operating Khulnasoft at scale.

The provisioning of these disjoint containers is handled by the [Khulnasoft-Ansible](https://github.com/khulnasoft/khulnasoft-ansible) project. Refer to the [Khulnasoft-Ansible documentation](https://khulnasoft.github.io/khulnasoft-ansible/) and the [Ansible User Guide](https://docs.ansible.com/ansible/latest/user_guide/index.html) for more details.

---

### Table of Contents

* [Introduction](INTRODUCTION.md)
* [Getting Started](SETUP.md)
    * [Requirements](SETUP.md#requirements)
    * [Install](SETUP.md#install)
    * [Deploy](SETUP.md#deploy)
* [Examples](EXAMPLES.md)
* [Advanced Usage](ADVANCED.md)
    * [Runtime configuration](ADVANCED.md#runtime-configuration)
    * [Install apps](ADVANCED.md#install-apps)
    * [Apply Khulnasoft license](ADVANCED.md#apply-khulnasoft-license)
    * [Create custom configs](ADVANCED.md#create-custom-configs)
    * [Enable SmartStore](ADVANCED.md#enable-smartstore)
    * [Use a deployment server](ADVANCED.md#use-a-deployment-server)
    * [Deploy distributed topology](ADVANCED.md#deploy-distributed-topology)
    * [Enable SSL communication](ADVANCED.md#enable-ssl-internal-communication)
    * [Build from source](ADVANCED.md#build-from-source)
* [Persistent Storage](STORAGE_OPTIONS.md)
* [Architecture](ARCHITECTURE.md)
* [Troubleshooting](TROUBLESHOOTING.md)
* [Contributing](CONTRIBUTING.md)
* [Support](SUPPORT.md)
* [Changelog](CHANGELOG.md)
* [License](LICENSE.md)
