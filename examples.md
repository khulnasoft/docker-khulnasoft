# Examples

This section provides examples on how to run KhulnaSoft server in a container:
- using [docker commands](#run-khulnasoft-using-docker-commands)
- using [docker-compose](#run-khulnasoft-using-docker-compose)

To analyze a project check our [scanner docs](https://docs.khulnasoft.org/latest/analysis/overview/).

## Run KhulnaSoft using docker commands
Before you start KhulnaSoft, we recommend creating volumes to store KhulnaSoft data, logs, temporary data and extensions. If you don't do that, you can loose them when you decide to update to newer version of KhulnaSoft or upgrade to a higher KhulnaSoft edition. Commands to create the volumes: 
```bash
$> docker volume create --name khulnasoft_data
$> docker volume create --name khulnasoft_extensions
$> docker volume create --name khulnasoft_logs
$> docker volume create --name khulnasoft_temp
``` 

After that you can start the KhulnaSoft server (this example uses the Community Edition):
```bash
$> docker run \
    -v khulnasoft_data:/opt/khulnasoft/data \
    -v khulnasoft_extensions:/opt/khulnasoft/extensions \
    -v khulnasoft_logs:/opt/khulnasoft/logs \
    --name="khulnasoft" -p 9000:9000 khulnasoft:community
```
The above command starts KhulnaSoft with an embedded database. We recommend starting the instance with a separate database
by providing `KHULNASOFT_JDBC_URL`, `KHULNASOFT_JDBC_USERNAME` and `KHULNASOFT_JDBC_PASSWORD` like this:
```bash
$> docker run \
    -v khulnasoft_data:/opt/khulnasoft/data \
    -v khulnasoft_extensions:/opt/khulnasoft/extensions \
    -v khulnasoft_logs:/opt/khulnasoft/logs \
    -e KHULNASOFT_JDBC_URL="..." \
    -e KHULNASOFT_JDBC_USERNAME="..." \
    -e KHULNASOFT_JDBC_PASSWORD="..." \
    --name="khulnasoft" -p 9000:9000 khulnasoft:community
```

## Run KhulnaSoft using Docker Compose
### Requirements

 * Docker Engine 20.10+
 * Docker Compose 2.0.0+

### KhulnaSoft with Postgres:

Go to [this directory](example-compose-files/sq-with-h2) to run KhulnaSoft in development mode or [this directory](example-compose-files/sq-with-postgres) to run both KhulnaSoft and PostgreSQL. Then run [docker-compose](https://github.com/docker/compose):

```bash
$ docker-compose up
```

To restart KhulnaSoft container (for example after upgrading or installing a plugin):

```bash
$ docker-compose restart khulnasoft
```