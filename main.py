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

ENVIRONMENT_NAME = 'Sanjeev_Nomura_SM'
DEPLOYMENT_NAME = 'Sanjeev_Nomura_TB'
# Get environment variables
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK')
EMAL_ADDRESS = os.environ.get('EMAL_ADDRESS')

config = configparser.ConfigParser()
config.read('dataops.properties')

CRED_ID = config.get("DEFAULT", "CRED_ID")
CRED_TOKEN = config.get("DEFAULT", "CRED_TOKEN")

start_time = time.time()
warnings.simplefilter("ignore")

# Connect to the StreamSets DataOps Platform.
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)


def create_deployment():
    # Instantiate an EnvironmentBuilder instance to build an environment, and activate it.
    environment_builder = sch.get_environment_builder(environment_type='SELF')
    environment = environment_builder.build(environment_name=ENVIRONMENT_NAME,
                                            environment_type='SELF',
                                            environment_tags=['sanju'],
                                            allow_nightly_engine_builds=False)
    # Add the environment and activate it
    sch.add_environment(environment)
    sch.activate_environment(environment)

    # Instantiate the DeploymentBuilder instance to build the deployment
    deployment_builder = sch.get_deployment_builder(deployment_type='SELF')

    # Build the deployment and specify the Sample Environment created previously.
    deployment = deployment_builder.build(deployment_name=DEPLOYMENT_NAME,
                                          deployment_type='SELF',
                                          environment=environment,
                                          engine_type='DC',
                                          engine_version='4.4.0',
                                          deployment_tags=['sanju'])
    # Deployment type (Docker/Tarball)
    # deployment.install_type = 'DOCKER'
    deployment.install_type = 'TARBALL'

    # Optional - add sample stage libs
    deployment.engine_configuration.stage_libs = ['jdbc']
    deployment.engine_configuration.stage_libs = ['aws']
    deployment.engine_instances = 1

    # Add the deployment to SteamSets DataOps Platform, and start it
    sch.add_deployment(deployment)

    deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    # retrieve deployment configs
    sdc_properties = javaproperties.loads(
        deployment.engine_configuration.advanced_configuration.data_collector_configuration)
    # Adding runtime properties
    new_properties = {'runtime.conf_aws_secret_group': 'all@CS',
                      'runtime.conf_mysql_tableName': 'flights',
                      'runtime.conf_mysql_schemaName': 'sanju'
                      #'runtime.conf_slack_url': {SLACK_WEBHOOK}
                      }
    sdc_properties.update(new_properties)
    # override engine configs
    sdc_properties['production.maxBatchSize'] = '100000'
    if platform == "darwin":
        sdc_properties['sdc.base.http.url'] = '=http://localhost:18630'

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
    java_config.java_options = '-Xdebug'
    java_config.java_options = '-Dcom.sun.management.jmxremote'
    java_config.java_options = '-Dcom.sun.management.jmxremote.port = 3333'
    java_config.java_options = '-Dcom.sun.management.jmxremote.local.only = false'
    java_config.java_options = '-Dcom.sun.management.jmxremote.authenticate = false'
    java_config.java_options = '-Dcom.sun.management.jmxremote.ssl = false'

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
    #sdc_properties['xmail.username'] = EMAL_ADDRESS
    #sdc_properties['xmail.from.address'] = EMAL_ADDRESS

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
    current_engine_version = deployment.engine_configuration.engine_version
    #f.write('\nsource ~/.bash_profile\n')
    f.write(f'\nsudo echo $GMAIL  > $HOME/.streamsets/install/dc/streamsets-datacollector-{current_engine_version}/etc/email-password.txt\n')
    f.close()
    os.chmod("install_script.sh", stat.S_IRWXU)
    os.system("sh install_script.sh")


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
    java_config.java_options = '-Xdebug'
    java_config.java_options = '-Dcom.sun.management.jmxremote'
    java_config.java_options = '-Dcom.sun.management.jmxremote.port = 3333'
    java_config.java_options = '-Dcom.sun.management.jmxremote.local.only = false'
    java_config.java_options = '-Dcom.sun.management.jmxremote.authenticate = false'
    java_config.java_options = '-Dcom.sun.management.jmxremote.ssl = false'

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
    sdc_properties['xmail.username'] = EMAL_ADDRESS
    sdc_properties['xmail.from.address'] = EMAL_ADDRESS

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties
    sch.update_deployment(deployment)
    # persist changes to the deployment
    sch.update_deployment(deployment)
    sch.stop_deployment(deployment)
    sch.start_deployment(deployment)


create_deployment()

