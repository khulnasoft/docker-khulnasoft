#!/bin/bash

# Copyright 2018 Khulnasoft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

setup() {
	# Check if the user accepted the license
	if [[ "$KHULNASOFT_START_ARGS" != *"--accept-license"* ]]; then
		printf "License not accepted, please ensure the environment variable KHULNASOFT_START_ARGS contains the '--accept-license' flag\n"
		printf "For example: docker run -e KHULNASOFT_START_ARGS=--accept-license khulnasoft/universalforwarder\n\n"
		printf "For additional information and examples, see the help: docker run -it khulnasoft/universalforwarder help\n"
		exit 1
	fi
}

teardown() {
	# Always run the stop command on termination
	if [ `whoami` != "${KHULNASOFT_USER}" ]; then
		RUN_AS_KHULNASOFT="sudo -u ${KHULNASOFT_USER}"
	fi
	${RUN_AS_KHULNASOFT} ${KHULNASOFT_HOME}/bin/khulnasoft stop || true
}

trap teardown SIGINT SIGTERM

prep_ansible() {
	cd ${KHULNASOFT_ANSIBLE_HOME}
	if [ `whoami` == "${KHULNASOFT_USER}" ]; then
		sed -i -e "s,^become\\s*=.*,become = false," ansible.cfg
	fi
	if [[ "$DEBUG" == "true" ]]; then
		ansible-playbook --version
		python inventory/environ.py --write-to-file
		cat /opt/container_artifact/ansible_inventory.json 2>/dev/null
		echo
	fi
}

watch_for_failure(){
	if [[ $? -eq 0 ]]; then
		sh -c "echo 'started' > ${CONTAINER_ARTIFACT_DIR}/khulnasoft-container.state"
	fi
	echo ===============================================================================
	echo
	echo Ansible playbook complete, will begin streaming var/log/khulnasoft/khulnasoftd_stderr.log
	echo
	user_permission_change
	if [ `whoami` != "${KHULNASOFT_USER}" ]; then
		RUN_AS_KHULNASOFT="sudo -u ${KHULNASOFT_USER}"
	fi
	# Any crashes/errors while Khulnasoft is running should get logged to khulnasoftd_stderr.log and sent to the container's stdout
	if [ -z "$KHULNASOFT_TAIL_FILE" ]; then
		${RUN_AS_KHULNASOFT} tail -n 0 -f ${KHULNASOFT_HOME}/var/log/khulnasoft/khulnasoftd_stderr.log &
	else
		${RUN_AS_KHULNASOFT} tail -n 0 -f ${KHULNASOFT_TAIL_FILE} &
	fi
	wait
}

create_defaults() {
	createdefaults.py
}

start_and_exit() {
	if [ -z "$KHULNASOFT_PASSWORD" ]
	then
		echo "WARNING: No password ENV var.  Stack may fail to provision if khulnasoft.password is not set in ENV or a default.yml"
	fi
	sh -c "echo 'starting' > ${CONTAINER_ARTIFACT_DIR}/khulnasoft-container.state"
	setup
	prep_ansible
	ansible-playbook $ANSIBLE_EXTRA_FLAGS -i inventory/environ.py -l localhost site.yml
}

start() {
	start_and_exit
	watch_for_failure
}

restart(){
	sh -c "echo 'restarting' > ${CONTAINER_ARTIFACT_DIR}/khulnasoft-container.state"
	prep_ansible
	${KHULNASOFT_HOME}/bin/khulnasoft stop 2>/dev/null || true
	ansible-playbook -i inventory/environ.py -l localhost start.yml
	watch_for_failure
}

user_permission_change(){
	if [[ "$STEPDOWN_ANSIBLE_USER" == "true" ]]; then
		bash -c "sudo deluser -q ansible sudo"
	fi
}

help() {
	cat << EOF
  ____        _             _      __
 / ___| _ __ | |_   _ _ __ | | __  \ \\
 \___ \| '_ \| | | | | '_ \| |/ /   \ \\
  ___) | |_) | | |_| | | | |   <    / /
 |____/| .__/|_|\__,_|_| |_|_|\_\  /_/
       |_|
========================================

Environment Variables:
  * KHULNASOFT_USER - user under which to run Khulnasoft (default: khulnasoft)
  * KHULNASOFT_GROUP - group under which to run Khulnasoft (default: khulnasoft)
  * KHULNASOFT_HOME - home directory where Khulnasoft gets installed (default: /opt/khulnasoft)
  * KHULNASOFT_START_ARGS - arguments to pass into the Khulnasoft start command; you must include '--accept-license' to start Khulnasoft (default: none)
  * KHULNASOFT_PASSWORD - password to log into this Khulnasoft instance, you must include a password (default: none)
  * KHULNASOFT_STANDALONE_URL, KHULNASOFT_INDEXER_URL, ... - comma-separated list of resolvable aliases to properly bring-up a distributed environment.
                                                     This is optional for the UF, but necessary if you want to forward logs to another containerized Khulnasoft instance
  * KHULNASOFT_BUILD_URL - URL to a Khulnasoft Universal Forwarder build which will be installed (instead of the image's default build)
  * KHULNASOFT_DEPLOYMENT_SERVER - A network alias to Khulnasoft deployment server
  * KHULNASOFT_ADD - '<monitor|add> <what_to_monitor|what_to_add>' - list of monitors separated by commas
  * KHULNASOFT_CMD - 'any khulnasoft command' - execute any khulnasoft commands separated by commas
  * KHULNASOFT_BEFORE_START_CMD - 'any khulnasoft command to execute before Khulnasoft starts' - execute any khulnasoft commands separated by commas


EOF
	exit 1
}

case "$1" in
	start|start-service)
		shift
		start $@
		;;
	start-and-exit)
		shift
		start_and_exit $@
		;;
	create-defaults)
		create_defaults
		;;
	restart)
		shift
		restart $@
		;;
	no-provision)
		user_permission_change
		tail -n 0 -f /etc/hosts &
		wait
		;;
	bash|khulnasoft-bash)
		/bin/bash --init-file ${KHULNASOFT_HOME}/bin/setKhulnasoftEnv
		;;
	help)
		shift
		help $@
		;;
	*)
		shift
		help $@
		;;
esac
