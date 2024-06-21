#!/usr/bin/env python
# encoding: utf-8

import pytest
import time
import re
import os
import tarfile
import docker
import json
import urllib
import yaml
import subprocess
from shutil import copy, copytree, rmtree
from executor import Executor
from docker.types import Mount
# Code to suppress insecure https warnings
import urllib3
from urllib3.exceptions import InsecureRequestWarning, SubjectAltNameWarning
urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(SubjectAltNameWarning)


global PLATFORM
PLATFORM = "debian-9"
OLD_KHULNASOFT_VERSION = "7.3.4"

def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    option_value = metafunc.config.option.platform
    global PLATFORM
    PLATFORM = option_value


class TestDockerKhulnasoft(Executor):

    @classmethod
    def setup_class(cls):
        super(TestDockerKhulnasoft, cls).setup_class(PLATFORM)

    def setup_method(self, method):
        # Make sure all running containers are removed
        self._clean_docker_env()
        self.compose_file_name = None
        self.project_name = None
        self.DIR = None

    def teardown_method(self, method):
        if self.compose_file_name and self.project_name:
            if self.DIR:
                command = "docker-compose -p {} -f {} down --volumes --remove-orphans".format(self.project_name, os.path.join(self.DIR, self.compose_file_name))
            else:
                command = "docker-compose -p {} -f test_scenarios/{} down --volumes --remove-orphans".format(self.project_name, self.compose_file_name)
            out, err, rc = self._run_command(command)
            self._clean_docker_env()
        if self.DIR:
            try:
                rmtree(self.DIR)
            except OSError:
                pass
        self.compose_file_name, self.project_name, self.DIR = None, None, None

    def test_khulnasoft_entrypoint_help(self):
        # Run container
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="help")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "KHULNASOFT_HOME - home directory where Khulnasoft gets installed (default: /opt/khulnasoft)" in output
        assert "Examples:" in output
    
    def test_khulnasoft_ulimit(self):
        cid = None
        try:
            # Run container
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="no-provision")
            cid = cid.get("Id")
            self.client.start(cid)
            # Wait a bit
            time.sleep(5)
            # If the container is still running, we should be able to exec inside
            # Check that nproc limits are unlimited
            exec_command = self.client.exec_create(cid, "sudo -u khulnasoft bash -c 'ulimit -u'")
            std_out = self.client.exec_start(exec_command)
            assert "unlimited" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_khulnasoft_entrypoint_create_defaults(self):
        # Run container
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "home: /opt/khulnasoft" in output
        assert "password: " in output
        assert "secret: " in output
    
    def test_khulnasoft_entrypoint_start_no_password(self):
        # Run container
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="start",
                                           environment={"KHULNASOFT_START_ARGS": "nothing"})
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "WARNING: No password ENV var." in output

    def test_khulnasoft_entrypoint_start_no_accept_license(self):
        # Run container
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="start",
                                           environment={"KHULNASOFT_PASSWORD": "something", "KHULNASOFT_START_ARGS": "nothing"})
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "License not accepted, please ensure the environment variable KHULNASOFT_START_ARGS contains the '--accept-license' flag" in output

    def test_khulnasoft_entrypoint_no_provision(self):
        cid = None
        try:
            # Run container
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="no-provision")
            cid = cid.get("Id")
            self.client.start(cid)
            # Wait a bit
            time.sleep(5)
            # If the container is still running, we should be able to exec inside
            # Check that the git SHA exists in /opt/ansible
            exec_command = self.client.exec_create(cid, "cat /opt/ansible/version.txt")
            std_out = self.client.exec_start(exec_command)
            assert len(std_out.strip()) == 40
            # Check that the wrapper-example directory does not exist
            exec_command = self.client.exec_create(cid, "ls /opt/ansible/")
            std_out = self.client.exec_start(exec_command)
            assert "wrapper-example" not in std_out
            assert "docs" not in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        if cid:
            self.client.remove_container(cid, v=True, force=True)

    def test_khulnasoft_uid_gid(self):
        cid = None
        try:
            # Run container
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="no-provision")
            cid = cid.get("Id")
            self.client.start(cid)
            # Wait a bit
            time.sleep(5)
            # If the container is still running, we should be able to exec inside
            # Check that the git SHA exists in /opt/ansible
            exec_command = self.client.exec_create(cid, "id", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "uid=41812" in std_out
            assert "gid=41812" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        if cid:
            self.client.remove_container(cid, v=True, force=True)

    def test_compose_1so_trial(self):
        # Standup deployment
        self.compose_file_name = "1so_trial.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)

    def test_compose_1so_custombuild(self):
        # Standup deployment
        self.compose_file_name = "1so_custombuild.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)

    def test_compose_1so_namedvolumes(self):
        # TODO: We can do a lot better in this test - ex. check that data is persisted after restarts
        # Standup deployment
        self.compose_file_name = "1so_namedvolumes.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)

    def test_compose_1so_before_start_cmd(self):
        # Check that KHULNASOFT_BEFORE_START_CMD works for khulnasoft image
        # Standup deployment
        self.compose_file_name = "1so_before_start_cmd.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check Khulnasoftd using the new users
        assert self.check_khulnasoftd("admin2", "changemepls")
        assert self.check_khulnasoftd("admin3", "changemepls")
    
    def test_compose_1so_khulnasoft_add(self):
        # Check that KHULNASOFT_ADD works for khulnasoft image (role=standalone)
        # Standup deployment
        self.compose_file_name = "1so_khulnasoft_add_user.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check Khulnasoftd using the new users
        assert self.check_khulnasoftd("newman", "changemepls")

    def test_adhoc_1so_using_default_yml(self):
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        # Generate default.yml
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Change the admin user
        output = re.sub(r'  admin_user: admin', r'  admin_user: chewbacca', output)
        # Write the default.yml to a file
        os.mkdir(self.DIR)
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="start", ports=[8089], 
                                            volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[os.path.join(self.FIXTURES_DIR, khulnasoft_container_name) + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("chewbacca", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
                os.rmdir(self.DIR)
            except OSError:
                pass

    def test_adhoc_1so_khulnasoft_launch_conf(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_LAUNCH_CONF": "OPTIMISTIC_ABOUT_FILE_LOCKING=1,HELLO=WORLD"
                                                        },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check khulnasoft-launch.conf
            exec_command = self.client.exec_create(cid, r'cat /opt/khulnasoft/etc/khulnasoft-launch.conf', user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "OPTIMISTIC_ABOUT_FILE_LOCKING=1" in std_out
            assert "HELLO=WORLD" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_change_tailed_files(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_TAIL_FILE": "/opt/khulnasoft/var/log/khulnasoft/web_access.log /opt/khulnasoft/var/log/khulnasoft/first_install.log"
                                                        },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the tailed logs
            logs = self.client.logs(cid, tail=20)
            assert "==> /opt/khulnasoft/var/log/khulnasoft/first_install.log <==" in logs
            assert "==> /opt/khulnasoft/var/log/khulnasoft/web_access.log <==" in logs
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_password_from_file(self):
        # Create a khulnasoft container
        cid = None
        # From fixtures/pwfile
        filePW = "changeme123"
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            volumes=["/var/secrets/pwfile"], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": "/var/secrets/pwfile"
                                                        },
                                            host_config=self.client.create_host_config(binds=[self.FIXTURES_DIR + "/pwfile:/var/secrets/pwfile"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", filePW), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_reflexive_forwarding(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            # When adding KHULNASOFT_STANDALONE_URL to the standalone, we shouldn't have any situation where it starts forwarding/disables indexing
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name,
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_STANDALONE_URL": khulnasoft_container_name
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the decrypted pass4SymmKey
            exec_command = self.client.exec_create(cid, "ls /opt/khulnasoft/etc/system/local/", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "outputs.conf" not in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_khulnasoft_pass4symmkey(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name,
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_PASS4SYMMKEY": "wubbalubbadubdub"
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the decrypted pass4SymmKey
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/system/local/server.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            pass4SymmKey = re.search(r'\[general\].*?pass4SymmKey = (.*?)\n', std_out, flags=re.MULTILINE|re.DOTALL).group(1).strip()
            exec_command = self.client.exec_create(cid, "/opt/khulnasoft/bin/khulnasoft show-decrypted --value '{}'".format(pass4SymmKey), user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "wubbalubbadubdub" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_khulnasoft_secret_env(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name,
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_SECRET": "wubbalubbadubdub"
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/auth/khulnasoft.secret", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "wubbalubbadubdub" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_compose_1so_hec(self):
        # Standup deployment
        self.compose_file_name = "1so_hec.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        try:
            # token "abcd1234" is hard-coded within the 1so_hec.yaml compose
            assert log_json["all"]["vars"]["khulnasoft"]["hec"]["token"] == "abcd1234"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check HEC works - note the token "abcd1234" is hard-coded within the 1so_hec.yaml compose
        containers = self.client.containers(filters={"label": "com.docker.compose.project={}".format(self.project_name)})
        assert len(containers) == 1
        so1 = containers[0]
        khulnasoft_hec_port = self.client.port(so1["Id"], 8088)[0]["HostPort"]
        url = "https://localhost:{}/services/collector/event".format(khulnasoft_hec_port)
        kwargs = {"json": {"event": "hello world"}, "verify": False, "headers": {"Authorization": "Khulnasoft abcd1234"}}
        status, content = self.handle_request_retry("POST", url, kwargs)
        assert status == 200

    def test_adhoc_1so_preplaybook_with_sudo(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            volumes=["/playbooks/play.yml"], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_ANSIBLE_PRE_TASKS": "file:///playbooks/play.yml"
                                                        },
                                            host_config=self.client.create_host_config(binds=[self.FIXTURES_DIR + "/sudo_touch_dummy_file.yml:/playbooks/play.yml"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /tmp/i-am", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "batman" in std_out
            # Check file owner
            exec_command = self.client.exec_create(cid, r'stat -c \'%U\' /tmp/i-am')
            std_out = self.client.exec_start(exec_command)
            assert "root" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_postplaybook(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            volumes=["/playbooks/play.yml"], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_ANSIBLE_POST_TASKS": "file:///playbooks/play.yml"
                                                        },
                                            host_config=self.client.create_host_config(binds=[self.FIXTURES_DIR + "/touch_dummy_file.yml:/playbooks/play.yml"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /tmp/i-am", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "batman" in std_out
            # Check file owner
            exec_command = self.client.exec_create(cid, r'stat -c \'%U\' /tmp/i-am')
            std_out = self.client.exec_start(exec_command)
            assert "khulnasoft" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_postplaybook_with_sudo(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            volumes=["/playbooks/play.yml"], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_ANSIBLE_POST_TASKS": "file:///playbooks/play.yml"
                                                        },
                                            host_config=self.client.create_host_config(binds=[self.FIXTURES_DIR + "/sudo_touch_dummy_file.yml:/playbooks/play.yml"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /tmp/i-am", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "batman" in std_out
            # Check file owner
            exec_command = self.client.exec_create(cid, r'stat -c \'%U\' /tmp/i-am')
            std_out = self.client.exec_start(exec_command)
            assert "root" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
    
    def test_adhoc_1so_apps_location_in_default_yml(self):
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        DIR_EXAMPLE_APP = os.path.join(self.DIR, "khulnasoft_app_example")
        copytree(self.EXAMPLE_APP, DIR_EXAMPLE_APP)
        self.EXAMPLE_APP_TGZ = os.path.join(self.DIR, "khulnasoft_app_example.tgz")
        with tarfile.open(self.EXAMPLE_APP_TGZ, "w:gz") as tar:
            tar.add(DIR_EXAMPLE_APP, arcname=os.path.basename(DIR_EXAMPLE_APP))
        # Generate default.yml
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Change repl factor & search factor
        output = re.sub(r'  user: khulnasoft', r'  user: khulnasoft\n  apps_location: /tmp/defaults/khulnasoft_app_example.tgz', output)
        # Write the default.yml to a file
        # os.mkdir(self.DIR)
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            # Spin up this container, but also bind-mount the app in the fixtures directory
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="start-service", ports=[8089], 
                                            volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the app endpoint
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/servicesNS/nobody/khulnasoft_app_example/configs/conf-app/launcher?output_mode=json".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Let's go further and check app version
            output = json.loads(content)
            assert output["entry"][0]["content"]["version"] == "0.0.1"
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(self.EXAMPLE_APP_TGZ)
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1so_bind_mount_apps(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        DIR_EXAMPLE_APP = os.path.join(self.DIR, "khulnasoft_app_example")
        copytree(self.EXAMPLE_APP, DIR_EXAMPLE_APP)
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            # Spin up this container, but also bind-mount the app in the fixtures directory
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="start-service", ports=[8089], 
                                            volumes=["/tmp/defaults/", "/opt/khulnasoft/etc/apps/khulnasoft_app_example/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/", 
                                                                                              DIR_EXAMPLE_APP + ":/opt/khulnasoft/etc/apps/khulnasoft_app_example/"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the app endpoint
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/servicesNS/nobody/khulnasoft_app_example/configs/conf-app/launcher?output_mode=json".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Let's go further and check app version
            output = json.loads(content)
            assert output["entry"][0]["content"]["version"] == "0.0.1"
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1so_run_as_root(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name, user="root",
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_USER": "root",
                                                            "KHULNASOFT_GROUP": "root"
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check that root owns the khulnasoftd process
            exec_command = self.client.exec_create(cid, "ps -u root", user="root")
            std_out = self.client.exec_start(exec_command)
            assert "entrypoint.sh" in std_out
            assert "khulnasoftd" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_declarative_password(self):
        """
        This test is intended to check how the container gets provisioned with declarative passwords
        """
        # Create a khulnasoft container
        cid = None
        try:
            # Start the container using no-provision, otherwise we can't mutate the password
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            name=khulnasoft_container_name,
                                            command="no-provision",
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_DECLARATIVE_ADMIN_PASSWORD": "true"
                                                        },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Create a new /tmp/defaults/default.yml to change desired HEC settings
            exec_command = self.client.exec_create(cid, "mkdir -p /tmp/defaults", user="khulnasoft")
            self.client.exec_start(exec_command)
            exec_command = self.client.exec_create(cid, "touch /tmp/defaults/default.yml", user="khulnasoft")
            self.client.exec_start(exec_command)
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  password: thisisarealpassword123
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Execute ansible
            exec_command = self.client.exec_create(cid, "/sbin/entrypoint.sh start-and-exit")
            std_out = self.client.exec_start(exec_command)
            # Check khulnasoft with the initial password
            assert self.check_khulnasoftd("admin", "thisisarealpassword123", name=khulnasoft_container_name)
            # Mutate the password so that ansible changes it on the next run
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  password: thisisadifferentpw456
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Execute ansible again
            exec_command = self.client.exec_create(cid, "/sbin/entrypoint.sh start-and-exit")
            stdout = self.client.exec_start(exec_command)
            # Check khulnasoft with the initial password
            assert self.check_khulnasoftd("admin", "thisisadifferentpw456", name=khulnasoft_container_name)
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_declarative_password(self):
        """
        This test is intended to check how the container gets provisioned with declarative passwords
        """
        # Create a khulnasoft container
        cid = None
        try:
            # Start the container using no-provision, otherwise we can't mutate the password
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089], 
                                            name=khulnasoft_container_name,
                                            command="no-provision",
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_DECLARATIVE_ADMIN_PASSWORD": "true"
                                                        },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Create a new /tmp/defaults/default.yml to change desired HEC settings
            exec_command = self.client.exec_create(cid, "mkdir -p /tmp/defaults", user="khulnasoft")
            self.client.exec_start(exec_command)
            exec_command = self.client.exec_create(cid, "touch /tmp/defaults/default.yml", user="khulnasoft")
            self.client.exec_start(exec_command)
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  password: thisisarealpassword123
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Execute ansible
            exec_command = self.client.exec_create(cid, "/sbin/entrypoint.sh start-and-exit")
            std_out = self.client.exec_start(exec_command)
            # Check khulnasoft with the initial password
            assert self.check_khulnasoftd("admin", "thisisarealpassword123", name=khulnasoft_container_name)
            # Mutate the password so that ansible changes it on the next run
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  password: thisisadifferentpw456
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Execute ansible again
            exec_command = self.client.exec_create(cid, "/sbin/entrypoint.sh start-and-exit")
            stdout = self.client.exec_start(exec_command)
            # Check khulnasoft with the initial password
            assert self.check_khulnasoftd("admin", "thisisadifferentpw456", name=khulnasoft_container_name)
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_hec_idempotence(self):
        """
        This test is intended to check how the container gets provisioned with changing khulnasoft.hec.* parameters
        """
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089, 8088, 9999], 
                                            name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password
                                                        },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",), 8088: ("0.0.0.0",), 9999: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check that HEC endpoint is up - by default, the image will enable HEC
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert std_out == '''[http]
disabled = 0
'''
            exec_command = self.client.exec_create(cid, "netstat -tuln", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "tcp        0      0 0.0.0.0:8088            0.0.0.0:*               LISTEN" in std_out
            # Create a new /tmp/defaults/default.yml to change desired HEC settings
            exec_command = self.client.exec_create(cid, "mkdir -p /tmp/defaults", user="khulnasoft")
            self.client.exec_start(exec_command)
            exec_command = self.client.exec_create(cid, "touch /tmp/defaults/default.yml", user="khulnasoft")
            self.client.exec_start(exec_command)
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  hec:
    port: 9999
    token: hihihi
    ssl: False
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Restart the container - it should pick up the new HEC settings in /tmp/defaults/default.yml
            self.client.restart(khulnasoft_container_name)
            # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
            # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
            time.sleep(15)
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check the new HEC settings
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert '''[http]
disabled = 0
enableSSL = 0
port = 9999''' in std_out
            assert '''[http://khulnasoft_hec_token]
disabled = 0
token = hihihi''' in std_out
            exec_command = self.client.exec_create(cid, "netstat -tuln", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "tcp        0      0 0.0.0.0:9999            0.0.0.0:*               LISTEN" in std_out
            # Check HEC
            hec_port = self.client.port(cid, 9999)[0]["HostPort"]
            url = "http://localhost:{}/services/collector/event".format(hec_port)
            kwargs = {"json": {"event": "hello world"}, "headers": {"Authorization": "Khulnasoft hihihi"}}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
            # Modify the HEC configuration
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  hec:
    port: 8088
    token: byebyebye
    ssl: True
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Restart the container - it should pick up the new HEC settings in /tmp/defaults/default.yml
            self.client.restart(khulnasoft_container_name)
            # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
            # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
            time.sleep(15)
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check the new HEC settings
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert '''[http]
disabled = 0
enableSSL = 1
port = 8088''' in std_out
            assert '''[http://khulnasoft_hec_token]
disabled = 0
token = byebyebye''' in std_out
            exec_command = self.client.exec_create(cid, "netstat -tuln", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "tcp        0      0 0.0.0.0:8088            0.0.0.0:*               LISTEN" in std_out
            # Check HEC
            hec_port = self.client.port(cid, 8088)[0]["HostPort"]
            url = "https://localhost:{}/services/collector/event".format(hec_port)
            kwargs = {"json": {"event": "hello world"}, "headers": {"Authorization": "Khulnasoft byebyebye"}, "verify": False}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
            # Remove the token
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  hec:
    token:
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Restart the container - it should pick up the new HEC settings in /tmp/defaults/default.yml
            self.client.restart(khulnasoft_container_name)
            # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
            # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
            time.sleep(15)
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check the new HEC settings
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            # NOTE: The previous configuration still applies - we just deleted the former token
            assert '''[http]
disabled = 0
enableSSL = 1
port = 8088''' in std_out
            assert "[http://khulnasoft_hec_token]" not in std_out
            exec_command = self.client.exec_create(cid, "netstat -tuln", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "tcp        0      0 0.0.0.0:8088            0.0.0.0:*               LISTEN" in std_out
            # Disable HEC entirely
            exec_command = self.client.exec_create(cid, '''bash -c 'cat > /tmp/defaults/default.yml << EOL 
khulnasoft:
  hec:
    enable: False
EOL'
''', user="khulnasoft")
            self.client.exec_start(exec_command)
            # Restart the container - it should pick up the new HEC settings in /tmp/defaults/default.yml
            self.client.restart(khulnasoft_container_name)
            # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
            # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
            time.sleep(15)
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check the new HEC settings
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert '''[http]
disabled = 1''' in std_out
            exec_command = self.client.exec_create(cid, "netstat -tuln", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "tcp        0      0 0.0.0.0:8088            0.0.0.0:*               LISTEN" not in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_hec_ssl_disabled(self):
        # Create the container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089, 8088], 
                                            name=khulnasoft_container_name,
                                            environment={
                                                "DEBUG": "true", 
                                                "KHULNASOFT_START_ARGS": "--accept-license",
                                                "KHULNASOFT_HEC_TOKEN": "get-schwifty",
                                                "KHULNASOFT_HEC_SSL": "False",
                                                "KHULNASOFT_PASSWORD": self.password
                                            },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",), 8088: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check HEC
            hec_port = self.client.port(cid, 8088)[0]["HostPort"]
            url = "http://localhost:{}/services/collector/event".format(hec_port)
            kwargs = {"json": {"event": "hello world"}, "headers": {"Authorization": "Khulnasoft get-schwifty"}}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_khulnasoftd_no_ssl(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Update server ssl settings
        output = re.sub(r'''^  ssl:.*?password: null''', r'''  ssl:
    ca: null
    cert: null
    enable: false
    password: null''', output, flags=re.MULTILINE|re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_CERT_PREFIX": "http",
                                                            "KHULNASOFT_PASSWORD": p},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", p, name=khulnasoft_container_name, scheme="http")
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/system/local/server.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "enableKhulnasoftdSSL = false" in std_out
            # Check khulnasoftd using the custom certs
            mgmt_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "http://localhost:{}/services/server/info".format(mgmt_port)
            kwargs = {"auth": ("admin", p)}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1so_web_ssl(self):
        # Create the container
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = None
        try:
            # Commands to generate self-signed certificates for KhulnasoftWeb here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/Self-signcertificatesforKhulnasoftWeb
            cmd = "openssl req -x509 -newkey rsa:4096 -passout pass:abcd1234 -keyout {path}/key.pem -out {path}/cert.pem -days 365 -subj /CN=localhost".format(path=self.DIR)
            generate_certs = subprocess.check_output(cmd.split())
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_HTTP_ENABLESSL": "true",
                                                            "KHULNASOFT_HTTP_ENABLESSL_CERT": "/tmp/defaults/cert.pem",
                                                            "KHULNASOFT_HTTP_ENABLESSL_PRIVKEY": "/tmp/defaults/key.pem",
                                                            "KHULNASOFT_HTTP_ENABLESSL_PRIVKEY_PASSWORD": "abcd1234"
                                                            },
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check khulnasoftweb
            web_port = self.client.port(cid, 8000)[0]["HostPort"]
            url = "https://localhost:{}/".format(web_port)
            kwargs = {"verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "key.pem"))
                os.remove(os.path.join(self.DIR, "cert.pem"))
            except OSError:
                pass
 
    def test_compose_1so_java_oracle(self):
        # Standup deployment
        self.compose_file_name = "1so_java_oracle.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        try:
            assert log_json["all"]["vars"]["java_version"] == "oracle:8"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check if java is installed
        exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "java -version")
        std_out = self.client.exec_start(exec_command)
        assert "java version \"1.8.0" in std_out
        # Restart the container and make sure java is still installed
        self.client.restart("{}_so1_1".format(self.project_name))
        # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
        # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
        time.sleep(15)
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        assert self.check_khulnasoftd("admin", self.password)
        exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "java -version")
        std_out = self.client.exec_start(exec_command)
        assert "java version \"1.8.0" in std_out
 
    def test_compose_1so_java_openjdk8(self):
        # Standup deployment
        self.compose_file_name = "1so_java_openjdk8.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        try:
            assert log_json["all"]["vars"]["java_version"] == "openjdk:8"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check if java is installed
        exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "java -version")
        std_out = self.client.exec_start(exec_command)
        assert "openjdk version \"1.8.0" in std_out
        # Restart the container and make sure java is still installed
        self.client.restart("{}_so1_1".format(self.project_name))
        # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
        # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
        time.sleep(15)
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        assert self.check_khulnasoftd("admin", self.password)
        exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "java -version")
        std_out = self.client.exec_start(exec_command)
        assert "openjdk version \"1.8.0" in std_out
 

    def test_compose_1so_java_openjdk11(self):
        # Standup deployment
        self.compose_file_name = "1so_java_openjdk11.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        try:
            assert log_json["all"]["vars"]["java_version"] == "openjdk:11"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check if java is installed
        exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "java -version")
        std_out = self.client.exec_start(exec_command)
        assert "openjdk version \"11.0.2" in std_out
        # Restart the container and make sure java is still installed
        self.client.restart("{}_so1_1".format(self.project_name))
        # After restart, a container's logs are preserved. So, sleep in order for the self.wait_for_containers()
        # to avoid seeing the prior entrypoint's "Ansible playbook complete" string 
        time.sleep(15)
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        assert self.check_khulnasoftd("admin", self.password)
        exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "java -version")
        std_out = self.client.exec_start(exec_command)
        assert "openjdk version \"11.0.2" in std_out

    def test_compose_1so_enable_service(self):
        # Standup deployment
        self.compose_file_name = "1so_enable_service.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        try:
            # enable_service is set in the compose file
            assert log_json["all"]["vars"]["khulnasoft"]["enable_service"] == "true"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check if service is registered
        if 'debian' in PLATFORM:
            exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "sudo service khulnasoft status")
            std_out = self.client.exec_start(exec_command)
            assert "khulnasoftd is running" in std_out
        else:
            exec_command = self.client.exec_create("{}_so1_1".format(self.project_name), "stat /etc/init.d/khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "/etc/init.d/khulnasoft" in std_out
 
    def test_adhoc_1so_hec_custom_cert(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Commands to generate self-signed certificates for Khulnasoft here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates
        passphrase = "glootie"
        cmds = [    
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/ca.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -key {path}/ca.key -passin pass:{pw} -out {path}/ca.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -in {path}/ca.csr -sha512 -passin pass:{pw} -signkey {path}/ca.key -CAcreateserial -out {path}/ca.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/server.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -passin pass:{pw} -key {path}/server.key -out {path}/server.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -passin pass:{pw} -in {path}/server.csr -SHA256 -CA {path}/ca.pem -CAkey {path}/ca.key -CAcreateserial -out {path}/server.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "cat {path}/server.pem {path}/server.key {path}/ca.pem > {path}/cert.pem".format(path=self.DIR),
                    "cat {path}/server.pem {path}/ca.pem > {path}/cacert.pem".format(path=self.DIR)
            ]
        for cmd in cmds:
            execute_cmd = subprocess.check_output(["/bin/sh", "-c", cmd])
        # Update s2s ssl settings
        output = re.sub(r'''  hec:.*?    token: .*?\n''', r'''  hec:
    enable: True
    port: 8088
    ssl: True
    token: doyouwannadevelopanapp
    cert: /tmp/defaults/cert.pem
    password: {}\n'''.format(passphrase), output, flags=re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            password = "helloworld"
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8088, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": password},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8088: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", password, name=khulnasoft_container_name)
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "[http://khulnasoft_hec_token]" in std_out
            assert "serverCert = /tmp/defaults/cert.pem" in std_out
            assert "sslPassword = " in std_out
            # Check HEC using the custom certs
            hec_port = self.client.port(cid, 8088)[0]["HostPort"]
            url = "https://localhost:{}/services/collector/event".format(hec_port)
            kwargs = {"json": {"event": "hello world"}, "headers": {"Authorization": "Khulnasoft doyouwannadevelopanapp"}, "verify": "{}/cacert.pem".format(self.DIR)}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1so_khulnasofttcp_ssl(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        password = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert password and password != "null"
        # Commands to generate self-signed certificates for Khulnasoft here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates
        passphrase = "abcd1234"
        cmds = [    
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/ca.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -key {path}/ca.key -passin pass:{pw} -out {path}/ca.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -in {path}/ca.csr -sha512 -passin pass:{pw} -signkey {path}/ca.key -CAcreateserial -out {path}/ca.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/server.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -passin pass:{pw} -key {path}/server.key -out {path}/server.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -passin pass:{pw} -in {path}/server.csr -SHA256 -CA {path}/ca.pem -CAkey {path}/ca.key -CAcreateserial -out {path}/server.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "cat {path}/server.pem {path}/server.key {path}/ca.pem > {path}/cert.pem".format(path=self.DIR)
            ]
        for cmd in cmds:
            execute_cmd = subprocess.check_output(["/bin/sh", "-c", cmd])
        # Update s2s ssl settings
        output = re.sub(r'''  s2s:.*?ssl: false''', r'''  s2s:
    ca: /tmp/defaults/ca.pem
    cert: /tmp/defaults/cert.pem
    enable: true
    password: {}
    port: 9997
    ssl: true'''.format(passphrase), output, flags=re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": password},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", password, name=khulnasoft_container_name)
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/system/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "[khulnasofttcp-ssl:9997]" in std_out
            assert "serverCert = /tmp/defaults/cert.pem" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1so_khulnasoftd_custom_ssl(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        password = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert password and password != "null"
        # Commands to generate self-signed certificates for Khulnasoft here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates
        passphrase = "heyallyoucoolcatsandkittens"
        cmds = [    
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/ca.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -key {path}/ca.key -passin pass:{pw} -out {path}/ca.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -in {path}/ca.csr -sha512 -passin pass:{pw} -signkey {path}/ca.key -CAcreateserial -out {path}/ca.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/server.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -passin pass:{pw} -key {path}/server.key -out {path}/server.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -passin pass:{pw} -in {path}/server.csr -SHA256 -CA {path}/ca.pem -CAkey {path}/ca.key -CAcreateserial -out {path}/server.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "cat {path}/server.pem {path}/server.key {path}/ca.pem > {path}/cert.pem".format(path=self.DIR),
                    "cat {path}/server.pem {path}/ca.pem > {path}/cacert.pem".format(path=self.DIR)
            ]
        for cmd in cmds:
            execute_cmd = subprocess.check_output(["/bin/sh", "-c", cmd])
        # Update server ssl settings
        output = re.sub(r'''^  ssl:.*?password: null''', r'''  ssl:
    ca: /tmp/defaults/ca.pem
    cert: /tmp/defaults/cert.pem
    enable: true
    password: {}'''.format(passphrase), output, flags=re.MULTILINE|re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": password},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", password, name=khulnasoft_container_name)
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/system/local/server.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "sslRootCAPath = /tmp/defaults/ca.pem" in std_out
            assert "serverCert = /tmp/defaults/cert.pem" in std_out
            # Check khulnasoftd using the custom certs
            mgmt_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(mgmt_port)
            kwargs = {"auth": ("admin", password), "verify": "{}/cacert.pem".format(self.DIR)}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass
     
    def test_adhoc_1so_upgrade(self):
        # Pull the old image
        for line in self.client.pull("khulnasoft/khulnasoft:{}".format(OLD_KHULNASOFT_VERSION), stream=True, decode=True):
            continue
        # Create the "khulnasoft-old" container
        try:
            cid = None
            khulnasoft_container_name = self.generate_random_string()
            user, password = "admin", self.generate_random_string()
            cid = self.client.create_container("khulnasoft/khulnasoft:{}".format(OLD_KHULNASOFT_VERSION), tty=True, ports=[8089, 8088], hostname="khulnasoft",
                                            name=khulnasoft_container_name, environment={"DEBUG": "true", "KHULNASOFT_HEC_TOKEN": "qwerty", "KHULNASOFT_PASSWORD": password, "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(mounts=[Mount("/opt/khulnasoft/etc", "opt-khulnasoft-etc"), Mount("/opt/khulnasoft/var", "opt-khulnasoft-var")],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8088: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            containers = self.client.containers(filters={"label": "com.docker.compose.project={}".format(self.project_name), "name": khulnasoft_container_name})
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Add some data via HEC
            khulnasoft_hec_port = self.client.port(cid, 8088)[0]["HostPort"]
            url = "https://localhost:{}/services/collector/event".format(khulnasoft_hec_port)
            kwargs = {"json": {"event": "world never says hello back"}, "verify": False, "headers": {"Authorization": "Khulnasoft qwerty"}}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
            # Sleep to let the data index
            time.sleep(3)
            # Remove the "khulnasoft-old" container
            self.client.remove_container(cid, v=False, force=True)
            # Create the "khulnasoft-new" container re-using volumes
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089, 8000], hostname="khulnasoft",
                                            name=khulnasoft_container_name, environment={"DEBUG": "true", "KHULNASOFT_HEC_TOKEN": "qwerty", "KHULNASOFT_PASSWORD": password, "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(mounts=[Mount("/opt/khulnasoft/etc", "opt-khulnasoft-etc"), Mount("/opt/khulnasoft/var", "opt-khulnasoft-var")],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            containers = self.client.containers(filters={"label": "com.docker.compose.project={}".format(self.project_name), "name": khulnasoft_container_name})
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Run a search
            time.sleep(3)
            query = "search index=main earliest=-10m"
            meta, results = self._run_khulnasoft_query(cid, query, user, password)
            results = results["results"]
            assert len(results) == 1
            assert results[0]["_raw"] == "world never says hello back"
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1so_preplaybook(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, ports=[8089], 
                                            volumes=["/playbooks/play.yml"], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_ANSIBLE_PRE_TASKS": "file:///playbooks/play.yml"
                                                        },
                                            host_config=self.client.create_host_config(binds=[self.FIXTURES_DIR + "/touch_dummy_file.yml:/playbooks/play.yml"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /tmp/i-am", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "batman" in std_out
            # Check file owner
            exec_command = self.client.exec_create(cid, r'stat -c \'%U\' /tmp/i-am')
            std_out = self.client.exec_start(exec_command)
            assert "khulnasoft" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_compose_1so_apps(self):
        self.project_name = self.generate_random_string()
        # Tar the app before spinning up the scenario
        with tarfile.open(os.path.join(self.FIXTURES_DIR, "{}.tgz".format(self.project_name)), "w:gz") as tar:
            tar.add(self.EXAMPLE_APP, arcname=os.path.basename(self.EXAMPLE_APP))
        # Standup deployment
        self.compose_file_name = "1so_apps.yaml"
        container_count, rc = self.compose_up(apps_url="http://appserver/{}.tgz".format(self.project_name))
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_so1_1".format(self.project_name))
        self.check_common_keys(log_json, "so")
        try:
            assert log_json["all"]["vars"]["khulnasoft"]["apps_location"][0] == "http://appserver/{}.tgz".format(self.project_name)
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["default"] == "/opt/khulnasoft/etc/apps"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["deployment"] == "/opt/khulnasoft/etc/deployment-apps"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["httpinput"] == "/opt/khulnasoft/etc/apps/khulnasoft_httpinput"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["idxc"] == "/opt/khulnasoft/etc/master-apps"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["shc"] == "/opt/khulnasoft/etc/shcluster/apps"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_so1_1".format(self.project_name))
        self.check_ansible(output)
        # Check to make sure the app got installed
        containers = self.client.containers(filters={"label": "com.docker.compose.project={}".format(self.project_name)})
        assert len(containers) == 2
        for container in containers:
            # Skip the nginx container
            if "nginx" in container["Image"]:
                continue
            # Check the app endpoint
            khulnasoftd_port = self.client.port(container["Id"], 8089)[0]["HostPort"]
            url = "https://localhost:{}/servicesNS/nobody/khulnasoft_app_example/configs/conf-app/launcher?output_mode=json".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Let's go further and check app version
            output = json.loads(content)
            assert output["entry"][0]["content"]["version"] == "0.0.1"
        try:
            os.remove(os.path.join(self.FIXTURES_DIR, "{}.tgz".format(self.project_name)))
        except OSError:
            pass

    def test_adhoc_1so_custom_conf(self):
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        # Generate default.yml
        cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        password = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert password and password != "null"
        # Add a custom conf file
        output = re.sub(r'  group: khulnasoft', r'''  group: khulnasoft
  conf:
    user-prefs:
      directory: /opt/khulnasoft/etc/users/admin/user-prefs/local
      content:
        general:
          default_namespace: appboilerplate
          search_syntax_highlighting: dark''', output)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.KHULNASOFT_IMAGE_NAME, tty=True, command="start", ports=[8089], 
                                            volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoft/etc/users/admin/user-prefs/local/user-prefs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "[general]" in std_out
            assert "default_namespace = appboilerplate" in std_out
            assert "search_syntax_highlighting = dark" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
                rmtree(self.DIR)
            except OSError:
                pass

    def test_compose_1uf_apps(self):
        self.project_name = self.generate_random_string()
         # Tar the app before spinning up the scenario
        with tarfile.open(os.path.join(self.FIXTURES_DIR, "{}.tgz".format(self.project_name)), "w:gz") as tar:
            tar.add(self.EXAMPLE_APP, arcname=os.path.basename(self.EXAMPLE_APP))
        # Standup deployment
        self.compose_file_name = "1uf_apps.yaml"
        container_count, rc = self.compose_up(apps_url="http://appserver/{}.tgz".format(self.project_name))
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_uf1_1".format(self.project_name))
        self.check_common_keys(log_json, "uf")
        try:
            assert log_json["all"]["vars"]["khulnasoft"]["apps_location"][0] == "http://appserver/{}.tgz".format(self.project_name)
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["default"] == "/opt/khulnasoftforwarder/etc/apps"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["deployment"] == "/opt/khulnasoftforwarder/etc/deployment-apps"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["httpinput"] == "/opt/khulnasoftforwarder/etc/apps/khulnasoft_httpinput"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["idxc"] == "/opt/khulnasoftforwarder/etc/master-apps"
            assert log_json["all"]["vars"]["khulnasoft"]["app_paths"]["shc"] == "/opt/khulnasoftforwarder/etc/shcluster/apps"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_uf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check to make sure the app got installed
        containers = self.client.containers(filters={"label": "com.docker.compose.project={}".format(self.project_name)})
        assert len(containers) == 2
        for container in containers:
            # Skip the nginx container
            if "nginx" in container["Image"]:
                continue
            # Check the app endpoint
            khulnasoftd_port = self.client.port(container["Id"], 8089)[0]["HostPort"]
            url = "https://localhost:{}/servicesNS/nobody/khulnasoft_app_example/configs/conf-app/launcher?output_mode=json".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Let's go further and check app version
            output = json.loads(content)
            assert output["entry"][0]["content"]["version"] == "0.0.1"
        try:
            os.remove(os.path.join(self.FIXTURES_DIR, "{}.tgz".format(self.project_name)))
        except OSError:
            pass

    def test_uf_entrypoint_help(self):
        # Run container
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="help")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "KHULNASOFT_CMD - 'any khulnasoft command' - execute any khulnasoft commands separated by commas" in output

    def test_uf_entrypoint_create_defaults(self):
        # Run container
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "home: /opt/khulnasoft" in output
        assert "password: " in output
    
    def test_uf_entrypoint_start_no_password(self):
        # Run container
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="start",
                                           environment={"KHULNASOFT_START_ARGS": "nothing"})
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "WARNING: No password ENV var." in output
    
    def test_uf_entrypoint_start_no_accept_license(self):
        # Run container
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="start",
                                           environment={"KHULNASOFT_PASSWORD": "something", "KHULNASOFT_START_ARGS": "nothing"})
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        assert "License not accepted, please ensure the environment variable KHULNASOFT_START_ARGS contains the '--accept-license' flag" in output

    def test_uf_entrypoint_no_provision(self):
        cid = None
        try:
            # Run container
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="no-provision")
            cid = cid.get("Id")
            self.client.start(cid)
            # Wait a bit
            time.sleep(5)
            # If the container is still running, we should be able to exec inside
            # Check that the git SHA exists in /opt/ansible
            exec_command = self.client.exec_create(cid, "cat /opt/ansible/version.txt")
            std_out = self.client.exec_start(exec_command)
            assert len(std_out.strip()) == 40
            # Check that the wrapper-example directory does not exist
            exec_command = self.client.exec_create(cid, "ls /opt/ansible/")
            std_out = self.client.exec_start(exec_command)
            assert "wrapper-example" not in std_out
            assert "docs" not in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_uf_uid_gid(self):
        cid = None
        try:
            # Run container
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="no-provision")
            cid = cid.get("Id")
            self.client.start(cid)
            # Wait a bit
            time.sleep(5)
            # If the container is still running, we should be able to exec inside
            # Check that the git SHA exists in /opt/ansible
            exec_command = self.client.exec_create(cid, "id", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "uid=41812" in std_out
            assert "gid=41812" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_khulnasofttcp_ssl(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        password = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert password and password != "null"
        # Commands to generate self-signed certificates for Khulnasoft here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates
        passphrase = "abcd1234"
        cmds = [    
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/ca.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -key {path}/ca.key -passin pass:{pw} -out {path}/ca.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -in {path}/ca.csr -sha512 -passin pass:{pw} -signkey {path}/ca.key -CAcreateserial -out {path}/ca.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/server.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -passin pass:{pw} -key {path}/server.key -out {path}/server.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -passin pass:{pw} -in {path}/server.csr -SHA256 -CA {path}/ca.pem -CAkey {path}/ca.key -CAcreateserial -out {path}/server.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "cat {path}/server.pem {path}/server.key {path}/ca.pem > {path}/cert.pem".format(path=self.DIR)
            ]
        for cmd in cmds:
            execute_cmd = subprocess.check_output(["/bin/sh", "-c", cmd])
        # Update s2s ssl settings
        output = re.sub(r'''  s2s:.*?ssl: false''', r'''  s2s:
    ca: /tmp/defaults/ca.pem
    cert: /tmp/defaults/cert.pem
    enable: true
    password: {}
    port: 9997
    ssl: true'''.format(passphrase), output, flags=re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": password},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", password, name=khulnasoft_container_name)
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/system/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "[khulnasofttcp-ssl:9997]" in std_out
            assert "serverCert = /tmp/defaults/cert.pem" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1uf_khulnasoftd_custom_ssl(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        password = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert password and password != "null"
        # Commands to generate self-signed certificates for Khulnasoft here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates
        passphrase = "heyallyoucoolcatsandkittens"
        cmds = [    
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/ca.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -key {path}/ca.key -passin pass:{pw} -out {path}/ca.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -in {path}/ca.csr -sha512 -passin pass:{pw} -signkey {path}/ca.key -CAcreateserial -out {path}/ca.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/server.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -passin pass:{pw} -key {path}/server.key -out {path}/server.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -passin pass:{pw} -in {path}/server.csr -SHA256 -CA {path}/ca.pem -CAkey {path}/ca.key -CAcreateserial -out {path}/server.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "cat {path}/server.pem {path}/server.key {path}/ca.pem > {path}/cert.pem".format(path=self.DIR),
                    "cat {path}/server.pem {path}/ca.pem > {path}/cacert.pem".format(path=self.DIR)
            ]
        for cmd in cmds:
            execute_cmd = subprocess.check_output(["/bin/sh", "-c", cmd])
        # Update server ssl settings
        output = re.sub(r'''^  ssl:.*?password: null''', r'''  ssl:
    ca: /tmp/defaults/ca.pem
    cert: /tmp/defaults/cert.pem
    enable: true
    password: {}'''.format(passphrase), output, flags=re.MULTILINE|re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": password},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/system/local/server.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "sslRootCAPath = /tmp/defaults/ca.pem" in std_out
            assert "serverCert = /tmp/defaults/cert.pem" in std_out
            # Check khulnasoftd using the custom certs
            mgmt_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(mgmt_port)
            kwargs = {"auth": ("admin", password), "verify": "{}/cacert.pem".format(self.DIR)}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_adhoc_1uf_hec_custom_cert(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Commands to generate self-signed certificates for Khulnasoft here: https://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Security/ConfigureKhulnasoftforwardingtousesignedcertificates
        passphrase = "glootie"
        cmds = [    
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/ca.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -key {path}/ca.key -passin pass:{pw} -out {path}/ca.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -in {path}/ca.csr -sha512 -passin pass:{pw} -signkey {path}/ca.key -CAcreateserial -out {path}/ca.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "openssl genrsa -aes256 -passout pass:{pw} -out {path}/server.key 2048".format(pw=passphrase, path=self.DIR),
                    "openssl req -new -passin pass:{pw} -key {path}/server.key -out {path}/server.csr -subj /CN=localhost".format(pw=passphrase, path=self.DIR),
                    "openssl x509 -req -passin pass:{pw} -in {path}/server.csr -SHA256 -CA {path}/ca.pem -CAkey {path}/ca.key -CAcreateserial -out {path}/server.pem -days 3".format(pw=passphrase, path=self.DIR),
                    "cat {path}/server.pem {path}/server.key {path}/ca.pem > {path}/cert.pem".format(path=self.DIR),
                    "cat {path}/server.pem {path}/ca.pem > {path}/cacert.pem".format(path=self.DIR)
            ]
        for cmd in cmds:
            execute_cmd = subprocess.check_output(["/bin/sh", "-c", cmd])
        # Update s2s ssl settings
        output = re.sub(r'''  hec:.*?    token: .*?\n''', r'''  hec:
    enable: True
    port: 8088
    ssl: True
    token: doyouwannadevelopanapp
    cert: /tmp/defaults/cert.pem
    password: {}\n'''.format(passphrase), output, flags=re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            password = "helloworld"
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8088, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": password},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8088: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", password, name=khulnasoft_container_name)
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/apps/khulnasoft_httpinput/local/inputs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "[http://khulnasoft_hec_token]" in std_out
            assert "serverCert = /tmp/defaults/cert.pem" in std_out
            assert "sslPassword = " in std_out
            # Check HEC using the custom certs
            hec_port = self.client.port(cid, 8088)[0]["HostPort"]
            url = "https://localhost:{}/services/collector/event".format(hec_port)
            kwargs = {"json": {"event": "hello world"}, "headers": {"Authorization": "Khulnasoft doyouwannadevelopanapp"}, "verify": "{}/cacert.pem".format(self.DIR)}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_compose_1uf_enable_service(self):
        # Standup deployment
        self.compose_file_name = "1uf_enable_service.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_uf1_1".format(self.project_name))
        self.check_common_keys(log_json, "uf")
        try:
            # enable_service is set in the compose file
            assert log_json["all"]["vars"]["khulnasoft"]["enable_service"] == "true"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_uf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check if service is registered
        if 'debian' in PLATFORM:
            exec_command = self.client.exec_create("{}_uf1_1".format(self.project_name), "sudo service khulnasoft status")
            std_out = self.client.exec_start(exec_command)
            assert "khulnasoftd is running" in std_out
        else:
            exec_command = self.client.exec_create("{}_uf1_1".format(self.project_name), "stat /etc/init.d/khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "/etc/init.d/khulnasoft" in std_out

    def test_adhoc_1uf_khulnasoftd_no_ssl(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Update server ssl settings
        output = re.sub(r'''^  ssl:.*?password: null''', r'''  ssl:
    ca: null
    cert: null
    enable: false
    password: null''', output, flags=re.MULTILINE|re.DOTALL)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8000, 8089], 
                                               volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                               environment={"DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_CERT_PREFIX": "http",
                                                            "KHULNASOFT_PASSWORD": p},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",), 8000: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", p, name=khulnasoft_container_name, scheme="http")
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/system/local/server.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "enableKhulnasoftdSSL = false" in std_out
            # Check khulnasoftd using the custom certs
            mgmt_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "http://localhost:{}/services/server/info".format(mgmt_port)
            kwargs = {"auth": ("admin", p)}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_compose_1uf_before_start_cmd(self):
        # Check that KHULNASOFT_BEFORE_START_CMD works for khulnasoftforwarder image
        # Standup deployment
        self.compose_file_name = "1uf_before_start_cmd.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_uf1_1".format(self.project_name))
        self.check_common_keys(log_json, "uf")
        # Check container logs
        output = self.get_container_logs("{}_uf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check Khulnasoftd using the new users
        assert self.check_khulnasoftd("normalplebe", "newpassword")

    def test_compose_1uf_khulnasoft_add(self):
        # Check that KHULNASOFT_ADD works for khulnasoftforwarder image
        # Standup deployment
        self.compose_file_name = "1uf_khulnasoft_add_user.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_uf1_1".format(self.project_name))
        self.check_common_keys(log_json, "uf")
        # Check container logs
        output = self.get_container_logs("{}_uf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check Khulnasoftd using the new users
        assert self.check_khulnasoftd("elaine", "changemepls")
        assert self.check_khulnasoftd("kramer", "changemepls")

    def test_compose_1uf_khulnasoft_cmd(self):
        # Check that KHULNASOFT_ADD works for khulnasoftforwarder image
        # Standup deployment
        self.compose_file_name = "1uf_khulnasoft_cmd.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_uf1_1".format(self.project_name))
        self.check_common_keys(log_json, "uf")
        # Check container logs
        output = self.get_container_logs("{}_uf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check Khulnasoftd using the new users
        assert self.check_khulnasoftd("jerry", "changemepls")
        assert self.check_khulnasoftd("george", "changemepls")

    def test_adhoc_1uf_using_default_yml(self):
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        # Generate default.yml
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Change the admin user
        output = re.sub(r'  admin_user: admin', r'  admin_user: hansolo', output)
        # Write the default.yml to a file
        os.mkdir(self.DIR)
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="start", ports=[8089], 
                                            volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                    port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("hansolo", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
                os.rmdir(self.DIR)
            except OSError:
                pass

    def test_adhoc_1uf_hec_ssl_disabled(self):
        # Create the container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089, 8088], 
                                            name=khulnasoft_container_name,
                                            environment={
                                                "DEBUG": "true", 
                                                "KHULNASOFT_START_ARGS": "--accept-license",
                                                "KHULNASOFT_HEC_TOKEN": "get-schwifty",
                                                "KHULNASOFT_HEC_SSL": "false",
                                                "KHULNASOFT_PASSWORD": self.password
                                            },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",), 8088: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", self.password, name=khulnasoft_container_name)
            # Check HEC
            hec_port = self.client.port(cid, 8088)[0]["HostPort"]
            url = "http://localhost:{}/services/collector/event".format(hec_port)
            kwargs = {"json": {"event": "hello world"}, "headers": {"Authorization": "Khulnasoft get-schwifty"}}
            status, content = self.handle_request_retry("POST", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_change_tailed_files(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089], 
                                            name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_TAIL_FILE": "/opt/khulnasoftforwarder/var/log/khulnasoft/khulnasoftd_stderr.log /opt/khulnasoftforwarder/var/log/khulnasoft/first_install.log"
                                                        },
                                            host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the tailed logs
            logs = self.client.logs(cid, tail=20)
            assert "==> /opt/khulnasoftforwarder/var/log/khulnasoft/first_install.log <==" in logs
            assert "==> /opt/khulnasoftforwarder/var/log/khulnasoft/khulnasoftd_stderr.log <==" in logs
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_password_from_file(self):
        # Create a khulnasoft container
        cid = None
        # From fixtures/pwfile
        filePW = "changeme123"
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089], 
                                            volumes=["/var/secrets/pwfile"], name=khulnasoft_container_name,
                                            environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": "/var/secrets/pwfile"
                                                        },
                                            host_config=self.client.create_host_config(binds=[self.FIXTURES_DIR + "/pwfile:/var/secrets/pwfile"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", filePW), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_compose_1uf_hec(self):
        # Standup deployment
        self.compose_file_name = "1uf_hec.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_uf1_1".format(self.project_name))
        self.check_common_keys(log_json, "uf")
        try:
            # token "abcd1234" is hard-coded within the 1so_hec.yaml compose
            assert log_json["all"]["vars"]["khulnasoft"]["hec"]["token"] == "abcd1234"
        except KeyError as e:
            self.logger.error(e)
            raise e
        # Check container logs
        output = self.get_container_logs("{}_uf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check HEC works - note the token "abcd1234" is hard-coded within the 1so_hec.yaml compose
        containers = self.client.containers(filters={"label": "com.docker.compose.project={}".format(self.project_name)})
        assert len(containers) == 1
        uf1 = containers[0]
        khulnasoft_hec_port = self.client.port(uf1["Id"], 8088)[0]["HostPort"]
        url = "https://localhost:{}/services/collector/event".format(khulnasoft_hec_port)
        kwargs = {"json": {"event": "hello world"}, "verify": False, "headers": {"Authorization": "Khulnasoft abcd1234"}}
        status, content = self.handle_request_retry("POST", url, kwargs)
        assert status == 200

    def test_adhoc_1uf_khulnasoft_pass4symmkey(self):
        # Create a khulnasoft container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name,
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_PASS4SYMMKEY": "wubbalubbadubdub"
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check the decrypted pass4SymmKey
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/system/local/server.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            pass4SymmKey = re.search(r'\[general\].*?pass4SymmKey = (.*?)\n', std_out, flags=re.MULTILINE|re.DOTALL).group(1).strip()
            exec_command = self.client.exec_create(cid, "/opt/khulnasoftforwarder/bin/khulnasoft show-decrypted --value '{}'".format(pass4SymmKey), user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "wubbalubbadubdub" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_khulnasoft_secret_env(self):
        # Create a uf container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name,
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_SECRET": "wubbalubbadubdub"
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/auth/khulnasoft.secret", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "wubbalubbadubdub" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_bind_mount_apps(self):
        # Generate default.yml
        khulnasoft_container_name = self.generate_random_string()
        self.project_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        DIR_EXAMPLE_APP = os.path.join(self.DIR, "khulnasoft_app_example")
        copytree(self.EXAMPLE_APP, DIR_EXAMPLE_APP)
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        p = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert p and p != "null"
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            # Spin up this container, but also bind-mount the app in the fixtures directory
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="start-service", ports=[8089], 
                                            volumes=["/tmp/defaults/", "/opt/khulnasoftforwarder/etc/apps/khulnasoft_app_example/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/", 
                                                                                              DIR_EXAMPLE_APP + ":/opt/khulnasoftforwarder/etc/apps/khulnasoft_app_example/"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            assert self.check_khulnasoftd("admin", p, name=khulnasoft_container_name)
            # Check the app endpoint
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/servicesNS/nobody/khulnasoft_app_example/configs/conf-app/launcher?output_mode=json".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", p), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Let's go further and check app version
            output = json.loads(content)
            assert output["entry"][0]["content"]["version"] == "0.0.1"
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
            except OSError:
                pass

    def test_uf_ulimit(self):
        cid = None
        try:
            # Run container
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="no-provision")
            cid = cid.get("Id")
            self.client.start(cid)
            # Wait a bit
            time.sleep(5)
            # If the container is still running, we should be able to exec inside
            # Check that nproc limits are unlimited
            exec_command = self.client.exec_create(cid, "sudo -u khulnasoft bash -c 'ulimit -u'")
            std_out = self.client.exec_start(exec_command)
            assert "unlimited" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_adhoc_1uf_custom_conf(self):
        khulnasoft_container_name = self.generate_random_string()
        self.DIR = os.path.join(self.FIXTURES_DIR, khulnasoft_container_name)
        os.mkdir(self.DIR)
        # Generate default.yml
        cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="create-defaults")
        self.client.start(cid.get("Id"))
        output = self.get_container_logs(cid.get("Id"))
        self.client.remove_container(cid.get("Id"), v=True, force=True)
        # Get the password
        password = re.search(r"^  password: (.*?)\n", output, flags=re.MULTILINE|re.DOTALL).group(1).strip()
        assert password and password != "null"
        # Add a custom conf file
        output = re.sub(r'  group: khulnasoft', r'''  group: khulnasoft
  conf:
    user-prefs:
      directory: /opt/khulnasoftforwarder/etc/users/admin/user-prefs/local
      content:
        general:
          default_namespace: appboilerplate
          search_syntax_highlighting: dark''', output)
        # Write the default.yml to a file
        with open(os.path.join(self.DIR, "default.yml"), "w") as f:
            f.write(output)
        # Create the container and mount the default.yml
        cid = None
        try:
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, command="start", ports=[8089], 
                                            volumes=["/tmp/defaults/"], name=khulnasoft_container_name,
                                            environment={"DEBUG": "true", "KHULNASOFT_START_ARGS": "--accept-license"},
                                            host_config=self.client.create_host_config(binds=[self.DIR + ":/tmp/defaults/"],
                                                                                       port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check if the created file exists
            exec_command = self.client.exec_create(cid, "cat /opt/khulnasoftforwarder/etc/users/admin/user-prefs/local/user-prefs.conf", user="khulnasoft")
            std_out = self.client.exec_start(exec_command)
            assert "[general]" in std_out
            assert "default_namespace = appboilerplate" in std_out
            assert "search_syntax_highlighting = dark" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)
            try:
                os.remove(os.path.join(self.DIR, "default.yml"))
                rmtree(self.DIR)
            except OSError:
                pass

    def test_adhoc_1uf_run_as_root(self):
        # Create a uf container
        cid = None
        try:
            khulnasoft_container_name = self.generate_random_string()
            cid = self.client.create_container(self.UF_IMAGE_NAME, tty=True, ports=[8089], name=khulnasoft_container_name, user="root",
                                               environment={
                                                            "DEBUG": "true", 
                                                            "KHULNASOFT_START_ARGS": "--accept-license",
                                                            "KHULNASOFT_PASSWORD": self.password,
                                                            "KHULNASOFT_USER": "root",
                                                            "KHULNASOFT_GROUP": "root"
                                                        },
                                               host_config=self.client.create_host_config(port_bindings={8089: ("0.0.0.0",)})
                                            )
            cid = cid.get("Id")
            self.client.start(cid)
            # Poll for the container to be ready
            assert self.wait_for_containers(1, name=khulnasoft_container_name)
            # Check khulnasoftd
            khulnasoftd_port = self.client.port(cid, 8089)[0]["HostPort"]
            url = "https://localhost:{}/services/server/info".format(khulnasoftd_port)
            kwargs = {"auth": ("admin", self.password), "verify": False}
            status, content = self.handle_request_retry("GET", url, kwargs)
            assert status == 200
            # Check that root owns the khulnasoftd process
            exec_command = self.client.exec_create(cid, "ps -u root", user="root")
            std_out = self.client.exec_start(exec_command)
            assert "entrypoint.sh" in std_out
            assert "khulnasoftd" in std_out
        except Exception as e:
            self.logger.error(e)
            raise e
        finally:
            if cid:
                self.client.remove_container(cid, v=True, force=True)

    def test_compose_1hf_khulnasoft_add(self):
        # Check that KHULNASOFT_ADD works for khulnasoft image (role=heavy forwarder)
        # Standup deployment
        self.compose_file_name = "1hf_khulnasoft_add_user.yaml"
        self.project_name = self.generate_random_string()
        container_count, rc = self.compose_up()
        assert rc == 0
        # Wait for containers to come up
        assert self.wait_for_containers(container_count, label="com.docker.compose.project={}".format(self.project_name))
        # Check ansible inventory json
        log_json = self.extract_json("{}_hf1_1".format(self.project_name))
        self.check_common_keys(log_json, "hf")
        # Check container logs
        output = self.get_container_logs("{}_hf1_1".format(self.project_name))
        self.check_ansible(output)
        # Check Khulnasoftd on all the containers
        assert self.check_khulnasoftd("admin", self.password)
        # Check Khulnasoftd using the new users
        assert self.check_khulnasoftd("jerry", "seinfeld")
