## Data Stream Processor
[Khulnasoft Data Stream Processor](https://www.khulnasoft.com/en_us/software/stream-processing.html) is a separate service that can be used to collect and facilitate real-time stream processing. For more information, visit the [Khulnasoft Data Stream Processor documentation](https://docs.khulnasoft.com/Documentation/DSP).

The Khulnasoft Docker image supports native integration with DSP through forwarders. Both universal and heavy forwarders can be automatically provisioned to send traffic to DSP, wherein custom pipelines can be configured to redirect and reformat the data as desired.

## Navigation

* [Forwarding traffic](#forwarding-traffic)
  * [User-generated certificates](#user-generated-certificates)
  * [Auto-generated certificates](#auto-generated-certificates)
* [Defining pipelines ](#defining-pipelines)

## Forwarding Traffic
Khulnasoft DSP pipelines can be used to [process forwarder data](https://docs.khulnasoft.com/Documentation/DSP/1.1.0/User/SenddataUF), either from a `khulnasoft_universal_forwarder` or a `khulnasoft_heavy_forwarder` role.

You will need [`scloud`](https://github.com/khulnasoft/khulnasoft-cloud-sdk-go) before proceeding.

### User-generated certificates
In order to get data into DSP, you must generate a client certificate and register it to the DSP forwarder service. Instructions for this can be found [here](https://docs.khulnasoft.com/Documentation/DSP/1.1.0/Data/Forwarder), or as follows:
```bash
$ openssl genrsa -out my_forwarder.key 2048
$ openssl req -new -key "my_forwarder.key" -out "my_forwarder.csr" -subj "/C=US/ST=CA/O=my_organization/CN=my_forwarder/emailAddress=email@example.com"
$ openssl x509 -req -days 730 -in "my_forwarder.csr" -signkey "my_forwarder.key" -out "my_forwarder.pem" -sha256
$ cat my_forwarder.pem my_forwarder.key > my_forwarder-keys.pem
$ scloud forwarders add-certificate --pem "$(<my_forwarder.pem)" 
```

Once you have the resulting `my_forwarder-keys.pem`, this can be mounted into the container and used immediately. Refer to the following `docker-compose.yml` example below:
```yaml
version: "3.6"

services:
  hf1:
    image: khulnasoft/khulnasoft:8.0.5
    hostname: hf1
    environment:
      - KHULNASOFT_ROLE=khulnasoft_heavy_forwarder
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_PASSWORD=helloworld
      - KHULNASOFT_DSP_ENABLE=true
      - KHULNASOFT_DSP_CERT=/opt/khulnasoft/etc/auth/mycerts/my_forwarder-keys.pem
      - KHULNASOFT_DSP_SERVER=dsp-master-node.hostname:30001
    ports:
      - 8000
      - 8089
    volumes:
      - ./my_forwarder-keys.pem:/opt/khulnasoft/etc/auth/mycerts/my_forwarder-keys.pem
```

Alternatively, this can also be done using the `default.yml` as so:
```yaml
---
khulnasoft:
  dsp:
    enable: True
    server: dsp-master-node.hostname:30001
    cert: /opt/khulnasoft/etc/auth/mycerts/my_forwarder-keys.pem
  ...
```

### Auto-generated Certificates
If you're just getting your feet wet with DSP and these Docker images, it can be helpful to rely on the Docker image to generate the certificates for you. Using `KHULNASOFT_DSP_CERT=auto` or `khulnasoft.dsp.cert: auto` will let the container to create the certificate and print it out through the container's logs for you to register yourself:
```bash
$ scloud forwarders add-certificate --pem "<copied from cert printed to container stdout>" 
```

## Defining Pipelines
In addition to native support for sending data, the Docker image is also capable of configuring the pipeline in DSP which can be useful in declaratively defining the full end-to-end parsing and ingest 

You will need [`scloud`](https://github.com/khulnasoft/khulnasoft-cloud-sdk-go) before proceeding. In addition, you'll need an `scloud.toml` and `.scloud_context` with permissions enabled to read/write to your DSP installation.

Pipeline specifications are defined using [SPL2](https://docs.khulnasoft.com/Documentation/DSP/1.1.0/User/SPL2). Refer to the following `docker-compose.yml` example below:
```yaml
version: "3.6"

services:
  hf1:
    image: khulnasoft/khulnasoft:8.0.5
    hostname: hf1
    environment:
      - KHULNASOFT_ROLE=khulnasoft_heavy_forwarder
      - KHULNASOFT_START_ARGS=--accept-license
      - KHULNASOFT_PASSWORD=helloworld
      - KHULNASOFT_DSP_ENABLE=true
      - KHULNASOFT_DSP_CERT=auto
      - KHULNASOFT_DSP_SERVER=dsp-master-node.hostname:30001
      - KHULNASOFT_DSP_PIPELINE_NAME=ingest-example
      - KHULNASOFT_DSP_PIPELINE_DESC="Demo using forwarders as source"
      - KHULNASOFT_DSP_PIPELINE_SPEC='| from receive_from_forwarders("forwarders:all") | into index("", "main");'
    ports:
      - 8000
      - 8089
    volumes:
      - ./.scloud.toml:/home/khulnasoft/.scloud.toml
      - ./.scloud_context:/home/khulnasoft/.scloud_context
```

Alternatively, this can also be done using the `default.yml` as so:
```yaml
---
khulnasoft:
  dsp:
    enable: True
    server: dsp-master-node.hostname:30001
    cert: auto
    pipeline_name: ingest-example
    pipeline_desc: "Demo using forwarders as source"
    pipeline_spec: '| from receive_from_forwarders("forwarders:all") | into index("", "main");'
  ...
```