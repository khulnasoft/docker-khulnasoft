FROM eclipse-temurin:17-jre

LABEL org.opencontainers.image.url=https://github.com/KhulnaSoft/docker-khulnasoft

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    LC_ALL='en_US.UTF-8'

#
# KhulnaSoft setup
#
ARG KHULNASOFT_VERSION=10.3.0.82913
ARG KHULNASOFT_ZIP_URL=https://binaries.khulnasoft.com/CommercialDistribution/khulnasoft-datacenter/khulnasoft-datacenter-${KHULNASOFT_VERSION}.zip
ENV DOCKER_RUNNING="true" \
    JAVA_HOME='/opt/java/openjdk' \
    KHULNASOFT_HOME=/opt/khulnasoft \
    KHULNASOFT_VERSION="${KHULNASOFT_VERSION}" \
    SQ_DATA_DIR="/opt/khulnasoft/data" \
    SQ_EXTENSIONS_DIR="/opt/khulnasoft/extensions" \
    SQ_LOGS_DIR="/opt/khulnasoft/logs" \
    SQ_TEMP_DIR="/opt/khulnasoft/temp" \
    KHULNASOFT_CLUSTER_NODE_TYPE="application" \
    KHULNASOFT_CLUSTER_ENABLED="true"

RUN set -eux; \
    useradd --system --uid 1000 --gid 0 khulnasoft; \
    apt-get update; \
    apt-get --no-install-recommends -y install gnupg unzip curl bash fonts-dejavu iproute2; \
    echo "networkaddress.cache.ttl=5" >> "${JAVA_HOME}/conf/security/java.security"; \
    sed --in-place --expression="s?securerandom.source=file:/dev/random?securerandom.source=file:/dev/urandom?g" "${JAVA_HOME}/conf/security/java.security"; \
    # pub   2048R/D26468DE 2015-05-25
    #       Key fingerprint = F118 2E81 C792 9289 21DB  CAB4 CFCA 4A29 D264 68DE
    # uid                  khulnasoft_deployer (Khulnasoft Deployer) <infra@khulnasoft.com>
    # sub   2048R/06855C1D 2015-05-25
    for server in $(shuf -e hkps://keys.openpgp.org \
                            hkps://keyserver.ubuntu.com) ; do \
        gpg --batch --keyserver "${server}" --recv-keys 679F1EE92B19609DE816FDE81DB198F93525EC1A && break || : ; \
    done; \
    mkdir --parents /opt; \
    cd /opt; \
    curl --fail --location --output khulnasoft.zip --silent --show-error "${KHULNASOFT_ZIP_URL}"; \
    curl --fail --location --output khulnasoft.zip.asc --silent --show-error "${KHULNASOFT_ZIP_URL}.asc"; \
    gpg --batch --verify khulnasoft.zip.asc khulnasoft.zip; \
    unzip -q khulnasoft.zip; \
    mv "khulnasoft-${KHULNASOFT_VERSION}" khulnasoft; \
    rm khulnasoft.zip*; \
    rm -rf ${KHULNASOFT_HOME}/bin/*; \
    ln -s "${KHULNASOFT_HOME}/lib/khulnasoft-application-${KHULNASOFT_VERSION}.jar" "${KHULNASOFT_HOME}/lib/khulnasoft.jar"; \
    chmod -R 550 ${KHULNASOFT_HOME}; \
    chmod -R 770 "${SQ_DATA_DIR}" "${SQ_EXTENSIONS_DIR}" "${SQ_LOGS_DIR}" "${SQ_TEMP_DIR}"; \
    apt-get remove -y gnupg unzip; \
    rm -rf /var/lib/apt/lists/*;

COPY run.sh khulnasoft.sh ${KHULNASOFT_HOME}/docker/

WORKDIR ${KHULNASOFT_HOME}
EXPOSE 9000

USER khulnasoft
STOPSIGNAL SIGINT

ENTRYPOINT ["/opt/khulnasoft/docker/run.sh"]
CMD ["/opt/khulnasoft/docker/khulnasoft.sh"]
