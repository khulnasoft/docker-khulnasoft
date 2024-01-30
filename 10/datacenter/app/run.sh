#!/usr/bin/env bash

set -euo pipefail

HOSTNAME=$(hostname)
IP=$(ip -4 address show scope global | grep inet | awk '{ print $2 }' | head -n 1 | cut -d \/ -f 1)

declare -a sq_opts=()
set_prop() {
  if [ "$2" ]; then
    sq_opts+=("-D$1=$2")
  fi
}

# if nothing is passed, assume we want to run khulnasoft server
if [ "$#" == 0 ]; then
  set -- /opt/khulnasoft/docker/khulnasoft.sh
fi

# if first arg looks like a flag, assume we want to run khulnasoft server with flags
if [ "${1:0:1}" = '-' ]; then
    set -- /opt/khulnasoft/docker/khulnasoft.sh "$@"
fi

if [[ "$1" = '/opt/khulnasoft/docker/khulnasoft.sh' ]]; then

    #
    # Change log path to ensure every app node can write in their own directory
    # This resolves a cluttered log on docker-compose with scale > 1
    #
    if [ -z "${KHULNASOFT_PATH_LOGS:-}" ]
    then
        KHULNASOFT_CLUSTER_PATH_LOGS="logs/${HOSTNAME}"
        mkdir -p ${KHULNASOFT_HOME}/${KHULNASOFT_CLUSTER_PATH_LOGS}
    else
        KHULNASOFT_CLUSTER_PATH_LOGS="${KHULNASOFT_PATH_LOGS}/${HOSTNAME}"
        mkdir -p ${KHULNASOFT_CLUSTER_PATH_LOGS}}
    fi

    #
    # Set mandatory properties
    #
    set_prop "khulnasoft.cluster.node.host" "${IP:-}"
    set_prop "khulnasoft.path.logs" "${KHULNASOFT_CLUSTER_PATH_LOGS:-}"
    if [ ${#sq_opts[@]} -ne 0 ]; then
        set -- "$@" "${sq_opts[@]}"
    fi
fi

exec "$@"
