import configparser
import os
import stat
import time
import warnings
from sys import platform
import javaproperties
# Import the ControlHub class from the SDK.
from streamsets.sdk import ControlHub

# sys.path.insert(1, os.path.abspath('/Users/sanjeev/SDK_4x'))
config = configparser.ConfigParser()
config.read('dataops.properties')
CRED_ID = config.get("DEFAULT", "CRED_ID")
CRED_TOKEN = config.get("DEFAULT", "CRED_TOKEN")
ENVIRONMENT_NAME = config.get("DEFAULT", "ENVIRONMENT_NAME")
ENVIRONMENT_TYPE = config.get("DEFAULT", "ENVIRONMENT_TYPE")
ENVIRONMENT_TAGS = config.get("DEFAULT", "ENVIRONMENT_TAGS")
DEPLOYMENT_NAME = config.get("DEFAULT", "DEPLOYMENT_NAME")
DEPLOYMENT_TYPE = config.get("DEFAULT", "DEPLOYMENT_TYPE")
DEPLOYMENT_TAGS = config.get("DEFAULT", "DEPLOYMENT_TAGS")
ENGINE_TYPE = config.get("DEFAULT", "ENGINE_TYPE")
ENGINE_VERSION = config.get("DEFAULT", "ENGINE_VERSION")
INSTALL_TYPE = config.get("DEFAULT", "INSTALL_TYPE")

# ENVIRONMENT_NAME = 'Sanjeev_Nomura_SM'
# DEPLOYMENT_NAME = 'Sanjeev_Nomura_TB'
# Get environment variables
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK')
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')

start_time = time.time()
warnings.simplefilter("ignore")
# Connect to the StreamSets DataOps Platform.
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)


def create_deployment():
    # Instantiate an EnvironmentBuilder instance to build an environment, and activate it.
    environment_builder = sch.get_environment_builder(environment_type=ENVIRONMENT_TYPE)
    environment = environment_builder.build(environment_name=ENVIRONMENT_NAME,
                                            environment_type=ENVIRONMENT_TYPE,
                                            environment_tags=[f'{ENVIRONMENT_TAGS}'],
                                            allow_nightly_engine_builds=False)
    # Add the environment and activate it
    sch.add_environment(environment)
    sch.activate_environment(environment)

    # Instantiate the DeploymentBuilder instance to build the deployment
    deployment_builder = sch.get_deployment_builder(deployment_type=DEPLOYMENT_TYPE)

    # Build the deployment and specify the Sample Environment created previously.
    deployment = deployment_builder.build(deployment_name=DEPLOYMENT_NAME,
                                          deployment_type=DEPLOYMENT_TYPE,
                                          environment=environment,
                                          engine_type=ENGINE_TYPE,
                                          engine_version=ENGINE_VERSION,
                                          deployment_tags=[f'{DEPLOYMENT_TAGS}'])
    # Deployment type (Docker/Tarball)
    # deployment.install_type = 'DOCKER'
    deployment.install_type = INSTALL_TYPE
    deployment.engine_instances = 1
    # Add the deployment to SteamSets DataOps Platform, and start it
    sch.add_deployment(deployment)
    # deployment must be added before retrieving engine_version
    current_engine_version = deployment.engine_configuration.engine_version
    # retrieve deployment to make changes
    deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    # Optional - add sample stage libs
    deployment.engine_configuration.stage_libs = [
        f"kinesis:{current_engine_version}",
        f"aws:{current_engine_version}",
        f"apache-kafka_1_0:{current_engine_version}",
        f"apache-kafka_1_1:{current_engine_version}",
        f"apache-kafka_2_0:{current_engine_version}",
        f"apache-kafka_2_1:{current_engine_version}",
        f"apache-kafka_2_2:{current_engine_version}",
        f"apache-kafka_2_3:{current_engine_version}",
        f"apache-kafka_2_4:{current_engine_version}",
        f"apache-kafka_2_5:{current_engine_version}",
        f"apache-kafka_2_6:{current_engine_version}",
        f"apache-kafka_2_7:{current_engine_version}",
        f"apache-kafka_2_8:{current_engine_version}",
        f"apache-pulsar_2:{current_engine_version}",
        f"apache-solr_6_1_0:{current_engine_version}",
        f"aws-secrets-manager-credentialstore:{current_engine_version}",
        f"azure-keyvault-credentialstore:{current_engine_version}",
        f"azure:{current_engine_version}",
        f"basic:{current_engine_version}",
        f"cassandra_3:{current_engine_version}",
        f"cdp_7_1:{current_engine_version}",
        f"couchbase_5:{current_engine_version}",
        f"crypto:{current_engine_version}",
        f"cyberark-credentialstore:{current_engine_version}",
        f"dataformats:{current_engine_version}",
        f"dev:{current_engine_version}",
        f"elasticsearch_5:{current_engine_version}",
        f"elasticsearch_6:{current_engine_version}",
        f"elasticsearch_7:{current_engine_version}",
        f"emr_hadoop_2_8_3:{current_engine_version}",
        f"bigtable:{current_engine_version}",
        f"google-cloud:{current_engine_version}",
        f"google-secret-manager-credentialstore:{current_engine_version}",
        f"groovy_2_4:{current_engine_version}",
        f"influxdb_0_9:{current_engine_version}",
        f"influxdb_2_0:{current_engine_version}",
        f"jks-credentialstore:{current_engine_version}",
        f"jdbc-sap-hana:{current_engine_version}",
        f"jdbc:{current_engine_version}",
        f"jms:{current_engine_version}",
        f"jython_2_7:{current_engine_version}",
        f"kinetica_6_0:{current_engine_version}",
        f"kinetica_6_1:{current_engine_version}",
        f"kinetica_6_2:{current_engine_version}",
        f"kinetica_7_0:{current_engine_version}",
        f"mapr_6_1-mep6:{current_engine_version}",
        f"mapr_6_1:{current_engine_version}",
        f"mleap:{current_engine_version}",
        f"mongodb_4:{current_engine_version}",
        f"mongodb_3:{current_engine_version}",
        f"mysql-binlog:{current_engine_version}",
        f"omniture:{current_engine_version}",
        f"orchestrator:{current_engine_version}",
        f"rabbitmq:{current_engine_version}",
        f"redis:{current_engine_version}",
        f"salesforce:{current_engine_version}",
        f"tensorflow:{current_engine_version}",
        f"thycotic-credentialstore:{current_engine_version}",
        f"vault-credentialstore:{current_engine_version}",
        f"wholefile-transformer:{current_engine_version}",
        f"azure-synapse:1.1.0",
        f"collibra:1.0.0",
        f"databricks:1.5.0",
        f"google:1.0.0",
        f"greenplum:1.0.0",
        f"memsql:1.0.1",
        f"oracle:1.3.0",
        f"dataprotector:1.9.0",
        f"snowflake:1.9.0",
        f"sql-server-bdc:1.0.1",
        f"teradata:1.0.1"
    ]
    # print(deployment.engine_configuration._data['stageLibs'])
    # retrieve deployment configs
    sdc_properties = javaproperties.loads(
        deployment.engine_configuration.advanced_configuration.data_collector_configuration)
    # Adding runtime properties
    new_properties = {'runtime.conf_aws_secret_group': 'all@CS',
                      'runtime.conf_mysql_tableName': 'flights',
                      'runtime.conf_mysql_schemaName': 'sanju',
                      'runtime.conf_mysql_jdbc_url': 'jdbc:mysql://localhost:3306'
                                                     '/sanju '
                      }
    sdc_properties.update(new_properties)
    # override engine configs
    sdc_properties['production.maxBatchSize'] = '100000'
    sdc_properties['runtime.conf_slack_url'] = SLACK_WEBHOOK
    if platform == "darwin":
        print("##### Mac Os Detected #####")
        sdc_properties['sdc.base.http.url'] = 'http://localhost:18630'

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties
    # verify persisted config changes
    # deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    # print(javaproperties.loads(deployment.engine_configuration.advanced_configuration.data_collector_configuration)[
    #           'production.maxBatchSize'])

    # Update install type
    # expected_install_type = 'DOCKER'
    # deployment.install_type = expected_install_type

    # Update external_resource_location
    expected_external_resource_location = '/var/resources/externalResources.tgz'
    deployment.engine_configuration.external_resource_location = expected_external_resource_location

    # Update java configurations
    java_config = deployment.engine_configuration.java_configuration
    java_config.maximum_java_heap_size_in_mb = 4096
    java_config.minimum_java_heap_size_in_mb = 2048
    java_config.java_options = '-Xdebug -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=3333 ' \
                               '-Dcom.sun.management.jmxremote.local.only=false ' \
                               '-Dcom.sun.management.jmxremote.authenticate=false ' \
                               '-Dcom.sun.management.jmxremote.ssl=false '

    # TODO
    # Fix the credential store lib issue
    # Add runtime resources
    #

    # configure aws credential store
    cred_properties = javaproperties.loads(deployment.engine_configuration.advanced_configuration.credential_stores)
    cred_properties['credentialStores'] = 'aws'
    cred_properties['credentialStore.aws.config.region'] = 'us-west-2'  # AWS Region
    cred_properties['credentialStore.aws.config.security.method'] = 'instanceProfile'  # accessKeys or instanceProfile
    cred_properties = javaproperties.dumps(cred_properties)
    deployment.engine_configuration.advanced_configuration.credential_stores = cred_properties

    # configure SMTP
    sdc_properties = javaproperties.loads(
        deployment.engine_configuration.advanced_configuration.data_collector_configuration)
    sdc_properties['mail.smtp.host'] = 'smtp.gmail.com'
    sdc_properties['mail.smtp.port'] = '587'
    sdc_properties['mail.smtp.auth'] = 'true'
    sdc_properties['mail.smtp.starttls.enable'] = 'true'
    sdc_properties['mail.smtps.auth'] = 'true'
    sdc_properties['xmail.username'] = EMAIL_ADDRESS
    sdc_properties['xmail.from.address'] = EMAIL_ADDRESS

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties
    # persist changes to the deployment
    sch.update_deployment(deployment)
    sch.start_deployment(deployment)

    # TO DO
    # Kerberos setup / JAAS config

    install_script = deployment.install_script()
    f = open("install_script.sh", "w")
    f.write('ulimit -n 32768\n')
    f.write(install_script)
    # f.write('\nsource ~/.bash_profile\n')
    f.write(
        f'\nsudo echo $GMAIL  > $HOME/.streamsets/install/dc/streamsets-datacollector-{current_engine_version}/etc'
        f'/email-password.txt\n')
    f.close()
    os.chmod("install_script.sh", stat.S_IRWXU)
    os.system("sh install_script.sh")
    print("Time for completion: ", (time.time() - start_time), " secs")


def update_deployment():
    deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    # Update deployment name and tag/s
    deployment.deployment_name = 'Sanjeev_Nomura_SelfManaged'
    deployment.tags = deployment.tags + ['nomura']

    # Update stage libraries
    stage_libraries = deployment.engine_configuration.select_stage_libraries
    current_engine_version = deployment.engine_configuration.engine_version
    if deployment.engine_configuration.engine_type == 'DC':
        additional_stage_libs = [f'streamsets-datacollector-jython_2_7-lib:{current_engine_version}',
                                 f'streamsets-datacollector-jdbc-lib:{current_engine_version}']

    stage_libraries.extend(additional_stage_libs)

    sch.update_deployment(deployment)
    sch.stop_deployment(deployment)
    sch.start_deployment(deployment)


create_deployment()
