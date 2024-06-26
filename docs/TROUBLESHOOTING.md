## Navigation

* [Troubleshooting](#troubleshooting)
* [System Validation](#system-validation)
* [Khulnasoft Validation](#khulnasoft-validation)
* [Container Debugging](#container-debugging)
    * [Getting logs](#getting-logs)
    * [Interactive shell](#interactive-shell)
    * [Installing packages](#installing-packages)
    * [Debug variables](#debug-variables)
    * [No-provision](#no-provision)
    * [Generate Khulnasoft diag](#generate-khulnasoft-diag)
* [Contact](#contact)

## Troubleshooting
As with most asynchronous design patterns, troubleshooting can be an arduous task. However, there are some built-in utilities to that you can employ to make your lives easier.

## System Validation
The most important step in troubleshooting is to validate the environment your container runs in. Please ensure that the following questions are answered:
* Is Docker installed properly?
* Is the Docker daemon running?
* Are you using the overlay2 storage-driver?
* Can you run simple Linux images (ex. debian, centos, alpine, etc.)?
* Are you using the latest Khulnasoft image? Or is this an older image?
* Do the image hashes match?
* Are there any settings that could influence or limit the container's behavior (ex. kernel, hardware, etc.)?
* Are there other containers that might be impacting the running Khulnasoft containers (i.e. noisy neighbors)?

## Khulnasoft Validation
Please refer to the [setup/installation page](SETUP.md#install) for comprehensive documentation on what is required on the host before launching your Khulnasoft container. However, you may also want to verify that:
* Container environment variable names are spelled correctly
* Container environment variable values are spelled correctly
* Environment variables that accept filepaths and URLs exist

## Container Debugging
If you find your container gets into a state when it crashes immediately on boot, or it hits a crash-loop backoff failure mode, you may need to do some live debugging. Here is some advice to help you proceed and figure out exactly why your container keeps crashing

#### Getting logs
The logs are by far the best way to analyze what went wrong with your deployment or container. Because we rely heavily on the [khulnasoft-ansible](https://github.com/khulnasoft/khulnasoft-ansible) project underneath the hood of this image, it's very likely that your container hit a specific failure in the Ansible level. Grabbing the container's stdout/stderr will tell you at what point and at what play this exception occurred.

To check for container logs, you can run the following command:
```
$ docker logs <container_name/container_id>
```

Alternatively, it's also possible to stream logs so you can watch what happens during the provisioning process in real-time:
```
$ docker logs --follow <container_name/container_id>
$ docker logs -f <container_name/container_id>
```

#### Interactive shell
If your container is still running but in a bad state, you can try to debug by putting yourself within the context of that process.

To gain interactive shell access to the container's runtime as the khulnasoft user, you can run:
```
$ docker exec -it -u khulnasoft <container_name/container_id> /bin/bash
```

#### Installing packages
Once inside the container, you can install additional packages with the default package manager:
```
$ microdnf install <package_name>
```
Please note that the package installer `microdnf` is specific to the redhat-8 operating system. When building other operating systems, please research and use the recommended package manager. You can refer to `base/<operating_system>/install.sh` to see package installation examples for different operating systems.

#### Debug variables
There are some built-in environment variables to assist with troubleshooting. Please be aware that when using these variables, it is possible for sensitive keys and information to be shown on the container's stdout/stderr. If you are using any custom logging driver or solution that persists this information, we recommend disabling it for the duration of this debug session.

The two primary environment variables that may be of assistance are `DEBUG` and `ANSIBLE_EXTRA_FLAGS`.

In order to use `DEBUG`, create a container and define `DEBUG=true` as so:
```
$ docker run -it -e DEBUG=true -e KHULNASOFT_START_ARGS=--accept-license -e KHULNASOFT_PASSWORD=<password> khulnasoft/khulnasoft:latest
ansible-playbook 2.7.7
  config file = /opt/ansible/ansible.cfg
  configured module search path = [u'/opt/ansible/library', u'/opt/ansible/apps/library', u'/opt/ansible/ansible_commands']
  ansible python module location = /usr/lib/python2.7/dist-packages/ansible
  executable location = /usr/bin/ansible-playbook
  python version = 2.7.13 (default, Sep 26 2018, 18:42:22) [GCC 6.3.0 20170516]
{
    "_meta": {
        "hostvars": {
            "localhost": {
                "ansible_connection": "local"
            }
        }
    },
    ...
```

If you check the container logs for this particular container, you'll notice the entire object generated by the dynamic inventory script `environ.py` is printed out at the top. This is particularly useful if you need to validate that certain variables are defined accordingly and map to exactly what has been explicitly set. It also displays the Python version and Ansible version used, which will greatly help if you plan on submitting a [GitHub issue](https://github.com/khulnasoft/docker-khulnasoft/issues) to make it easy for others to reproduce.

The `ANSIBLE_EXTRA_FLAGS` is another help environment variable that can be used to display more information or output from Ansible. For instance, one practical application of this could be:
```
$ docker run -it -e "ANSIBLE_EXTRA_FLAGS=-vv" -e KHULNASOFT_START_ARGS=--accept-license -e KHULNASOFT_PASSWORD=<password> khulnasoft/khulnasoft:latest
ansible-playbook 2.7.7
  config file = /opt/ansible/ansible.cfg
  configured module search path = [u'/opt/ansible/library', u'/opt/ansible/apps/library', u'/opt/ansible/ansible_commands']
  ansible python module location = /usr/lib/python2.7/dist-packages/ansible
  executable location = /usr/bin/ansible-playbook
  python version = 2.7.13 (default, Sep 26 2018, 18:42:22) [GCC 6.3.0 20170516]
Using /opt/ansible/ansible.cfg as config file
/opt/ansible/inventory/environ.py did not meet host_list requirements, check plugin documentation if this is unexpected

PLAYBOOK: site.yml ************************************************************
1 plays in site.yml

PLAY [Run default Khulnasoft provisioning] ****************************************
Thursday 21 February 2019  00:50:55 +0000 (0:00:00.036)       0:00:00.036 *****

TASK [Gathering Facts] ********************************************************
task path: /opt/ansible/site.yml:2
ok: [localhost]
META: ran handlers
Thursday 21 February 2019  00:50:56 +0000 (0:00:01.148)       0:00:01.185 *****
```
With the above, you'll notice how much more rich and verbose the Ansible output becomes, simply by adding more verbosity to the actual Ansible execution.

#### No-provision
The `no-provision` is a fairly useless supported command - after launching the container, it won't run Ansible so Khulnasoft will not get installed or even setup. Instead, it tails a file to keep the instance up and running.

This `no-provision` keyword is an argument that gets passed into the container's entrypoint script, so you can use it in the following manner:
```
$ docker run -it -e KHULNASOFT_START_ARGS=--accept-license -e KHULNASOFT_PASSWORD=<password> -e KHULNASOFT_HEC_TOKEN=abcd1234 --name spldebug khulnasoft/khulnasoft:latest no-provision
```

While by itself this seems fairly useless, it can be a great way to debug and troubleshoot Ansible problems locally. In the case above, we've set a `KHULNASOFT_HEC_TOKEN` environment variable. Let's go inside of this container and kick off Ansible manually, and make sure that the HEC token is set properly and that Khulnasoft uses it:
```
$ docker exec -it spldebug bash
ansible@5f60f3164e69:/$ echo $KHULNASOFT_HEC_TOKEN
abcd1234
ansible@5f60f3164e69:/$ /sbin/entrypoint.sh start

PLAY [Run default Khulnasoft provisioning] ****************************************
Thursday 21 February 2019  01:09:50 +0000 (0:00:00.034)       0:00:00.034 *****

TASK [Gathering Facts] ********************************************************
ok: [localhost]
```

#### Generate Khulnasoft diag
A Khulnasoft diagnostic file (diag) is a dump of a Khulnasoft environment that shows how the instance is configured and how it has been operating. If you plan on working with Khulnasoft Support, you may be requested to generate a diag for them to assist you. For more information on what is contained in a diag, refer to this [topic](https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Troubleshooting/Generateadiag).

Generating a diag is only an option if:
1. The Khulnasoft container is active and running
2. Administrators are able to `docker exec` into said container
3. Khulnasoft itself has a bug/performance problem

To create this diag, run the following command:
```
$ docker exec -it -u khulnasoft <container_name/container_id> "${KHULNASOFT_HOME}/bin/khulnasoft diag"
```

Additionally, if your Docker container/hosts have access to https://www.khulnasoft.com you can now send the file directly to Khulnasoft Support by using the following command:
```
$ docker exec -it -u khulnasoft <container_name/container_id> "${KHULNASOFT_HOME}/bin/khulnasoft diag --upload --case-number=<case_num> --upload-user=<your_khulnasoft_id> --upload-password=<passwd> --upload-description='Monday diag, as requested'"
```

However, if you don't have direct access, you can manually copy the diag back to your host via `docker cp`:
```
$ docker cp <container_name/container_id>:/opt/khulnasoft/<filename> <location on your local machine>
```

## Contact
If you require additional assistance, please see the [support guidelines](SUPPORT.md#contact) on how to reach out to Khulnasoft Support with issues or questions.
