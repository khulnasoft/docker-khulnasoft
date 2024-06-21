## Navigation

* [Preface](#preface)
* [System requirements](#system-requirements)
* [Contact](#contact)
* [Support violation](#support-violation)

## Preface
Khulnasoft Enterprise contains many settings that allow customers to tailor their Khulnasoft environment. However, because not all settings apply to all customers, Khulnasoft will only support the most common subset of all configurations. Throughout this document, the term "supported" means you can contact Khulnasoft Support for assistance with issues.

## System requirements

If you intend for this containerized Khulnasoft Enterprise deployment to be supported in your Enterprise Support Agreement, you must verify you meet all of the requirements below. **Failure to do so will render your deployment in an unsupported state.** See [Support violation](#support-violation) below.

The following prerequisites and dependencies must be installed on each node you plan on deploying the container.
* Linux-based operating system, such as Debian, CentOS, and so on.
* Chipset:
    * `khulnasoft/khulnasoft` image supports x86-64 chipsets
    * `khulnasoft/universalforwarder` image supports both x86-64 and s390x chipsets
* Kernel version 4.x
* Docker engine:
    * Docker Enterprise Engine 17.06.2 or higher
    * Docker Community Engine 17.06.2 or higher

        **Note:** If you are using [podman](https://github.com/containers/libpod), [CRI-O](https://github.com/cri-o/cri-o), [containerd](https://github.com/containerd/containerd) or other container runtimes, please be aware that these are currently outside of our support/testing matrix. It's possible that this Docker image still works, although you may need to manually add the environment variable `KUBERNETES_SERVICE_HOST=kubernetes` to configure the provisioning hooks properly.
* [OverlayFS](https://docs.docker.com/storage/storagedriver/overlayfs-driver/) `overlay2` Docker daemon storage driver
    1. Edit `/etc/docker/daemon.json`. If it does not yet exist, create it.
    2. Assuming the file was empty, add the following contents:
        ```
        { "storage-driver": "overlay2" }
        ```
        **Note:** If you already have an existing JSON file, add only `"storage-driver": "overlay2"` as a key-value pair. Docker does not start if the `daemon.json` file contains badly-formed JSON.

### See also

* [Supported platforms for containerized Khulnasoft software environments](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Installation/Systemrequirements#Containerized_computing_platforms)
* [Recommended hardware and capacity](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Installation/Systemrequirements#Recommended_hardware)
* Basic instructions to [deploy and run Khulnasoft Enterprise inside containers](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Installation/DeployandrunKhulnasoftEnterpriseinsideDockercontainers)

## Contact
Khulnasoft Support only provides support for the single instance Khulnasoft Validated Architectures (S-Type), Universal Forwarders and Heavy Forwarders. For all other configurations, [contact Khulnasoft Professional Services](https://www.khulnasoft.com/en_us/support-and-services.html).

For additional support, you can:
* Post a question to [Khulnasoft Answers](http://answers.khulnasoft.com).
* [Join us on Slack](https://docs.khulnasoft.com/Documentation/Community/1.0/community/Chat#Join_us_on_Slack) and post in the [#docker](https://khulnasoft-usergroups.slack.com/messages/C1RH09ERM/) channel.

If you are a Khulnasoft Enterprise customer with a valid support entitlement contract and have a Khulnasoft-related question, you can
* Open a support case on the <https://www.khulnasoft.com/> support portal.

## Support violation
In the following conditions, Khulnasoft Support reserves the right to deem your installation unsupported and not provide assistance when issues arise:
* You do not have an active support contract.
* You are running Khulnasoft Enterprise and/or Khulnasoft Universal Forwarder in a container on a platform not officially supported by Khulnasoft.
* You are using features not officially supported by Khulnasoft.

In the event you fall into an unsupported state, you may find support on [Khulnasoft Answers](http://answers.khulnasoft.com) or through the open-source communities found on GitHub for this [docker-khulnasoft](https://github.com/khulnasoft/docker-khulnasoft) project or the related [khulnasoft-ansible](https://www.github.com/khulnasoft/khulnasoft-ansible) project.
