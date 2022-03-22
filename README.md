# Provisioning DataOps environment

### Pre-requisites
1. [Install](https://docs.streamsets.com/platform-sdk/learn/installation.html) StreamSets SDK for Python 
2. Create the following configuration files:

credentials.properties:
```
[DEFAULT]

[SECURITY]
CRED_ID=<SCH CRED_ID>
CRED_TOKEN=<SCH CRED_TOKEN>
```
deployment.conf:
```
[DEFAULT]
[DEPLOYMENT]
ENVIRONMENT_NAME=<ENVIRONMENT_NAME>
DEPLOYMENT_NAME=<DEPLOYMENT_NAME>
ENVIRONMENT_TYPE=<ENVIRONMENT_TYPE>
ENVIRONMENT_TAGS=<ENVIRONMENT_TAGS>
DEPLOYMENT_TYPE=SELF
DEPLOYMENT_TAGS=<DEPLOYMENT_TAGS>
ENGINE_TYPE=DC
ENGINE_VERSION=<>
ENGINE_INSTANCES=1
INSTALL_TYPE=TARBALL
MAX_HEAP=_optional_
MIN_HEAP=_optional_
SLACK_WEBHOOK=_optional_
EMAIL_ADDRESS=_optional_


[SDC_PROPERTIES]
production.maxBatchSize=_optional_
mail.smtp.host=_optional_
mail.smtp.port=_optional_
mail.smtp.auth=_optional_
mail.smtp.starttls.enable=_optional_
mail.smtps.auth=_optional_
xmail.username=_optional_
xmail.from.address=_optional_


[RUNTIME_RESOURCES]
runtime.conf_aws_secret_group=_optional_
runtime.conf_mysql_tableName=_optional_
runtime.conf_mysql_schemaName=_optional_
runtime.conf_mysql_jdbc_url=_optional_
runtime.conf_slack_url=_optional_

[CRED_STORE]
credentialStores=_optional_
credentialStore.aws.config.region=_optional_
credentialStore.aws.config.security.method=_optional_
```
java_options.conf:
```
-Xdebug
-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=<jmx.port>
-Dcom.sun.management.jmxremote.local.only=false
-Dcom.sun.management.jmxremote.authenticate=false
-Dcom.sun.management.jmxremote.ssl=false
```

enterprise_libs.conf:
```
azure-synapse:1.1.0
collibra:1.0.0
databricks:1.5.0
google:1.0.0
greenplum:1.0.0
memsql:1.0.1
oracle:1.3.0
dataprotector:1.9.0
snowflake:1.9.0
sql-server-bdc:1.0.1
teradata:1.0.1
```
partial_stage_libs.conf:
```
aws-secrets-manager-credentialstore
basic
dataformats
dev
jdbc
```
stage_libs.conf:
```
kinesis
aws
apache-kafka_1_0
apache-kafka_1_1
apache-kafka_2_0
apache-kafka_2_1
apache-kafka_2_2
apache-kafka_2_3
apache-kafka_2_4
apache-kafka_2_5
apache-kafka_2_6
apache-kafka_2_7
apache-kafka_2_8
apache-pulsar_2
apache-solr_6_1_0
aws-secrets-manager-credentialstore
azure-keyvault-credentialstore
azure
basic
cassandra_3
cdp_7_1
couchbase_5
crypto
cyberark-credentialstore
dataformats
dev
elasticsearch_5
elasticsearch_6
elasticsearch_7
emr_hadoop_2_8_3
bigtable
google-cloud
google-secret-manager-credentialstore
groovy_2_4
influxdb_0_9
influxdb_2_0
jks-credentialstore
jdbc-sap-hana
jdbc
jms
jython_2_7
kinetica_6_0
kinetica_6_1
kinetica_6_2
kinetica_7_0
mapr_6_1-mep6
mapr_6_1
mleap
mongodb_4
mongodb_3
mysql-binlog
omniture
orchestrator
rabbitmq
redis
salesforce
tensorflow
thycotic-credentialstore
vault-credentialstore
wholefile-transformer
```
3. Usage: ```python main.py  ``` to create/update/delete DataOps deployment



