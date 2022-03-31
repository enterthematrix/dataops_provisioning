import configparser
import os
import stat
import time
import warnings
from sys import platform
import javaproperties
# Import the ControlHub class from the SDK.
from streamsets.sdk import ControlHub

start_time = time.time()
# sys.path.insert(1, os.path.abspath('/Users/sanjeev/SDK_4x'))
config = configparser.ConfigParser()
config.optionxform = lambda option: option
config.read('credentials.properties')
CRED_ID = config.get("SECURITY", "CRED_ID")
CRED_TOKEN = config.get("SECURITY", "CRED_TOKEN")
SLACK_WEBHOOK = config.get("SECURITY", "SLACK_WEBHOOK")

config.read('deployment.conf')
ENVIRONMENT_NAME = config.get("DEPLOYMENT", "ENVIRONMENT_NAME")
ENVIRONMENT_TYPE = config.get("DEPLOYMENT", "ENVIRONMENT_TYPE")
ENVIRONMENT_TAGS = config.get("DEPLOYMENT", "ENVIRONMENT_TAGS")
DEPLOYMENT_NAME = config.get("DEPLOYMENT", "DEPLOYMENT_NAME")
DEPLOYMENT_TYPE = config.get("DEPLOYMENT", "DEPLOYMENT_TYPE")
DEPLOYMENT_TAGS = config.get("DEPLOYMENT", "DEPLOYMENT_TAGS")
ENGINE_TYPE = config.get("DEPLOYMENT", "ENGINE_TYPE")
ENGINE_VERSION = config.get("DEPLOYMENT", "ENGINE_VERSION")
INSTALL_TYPE = config.get("DEPLOYMENT", "INSTALL_TYPE")
ENGINE_INSTANCES = config.get("DEPLOYMENT", "ENGINE_INSTANCES")
MAX_HEAP = config.get("DEPLOYMENT", "MAX_HEAP")
MIN_HEAP = config.get("DEPLOYMENT", "MIN_HEAP")
EMAIL_ADDRESS = config.get("DEPLOYMENT", "EMAIL_ADDRESS")
DOCKER_NETWORK = config.get("DEPLOYMENT", "DOCKER_NETWORK")
DOCKER_PORTS = config.get("DEPLOYMENT", "DOCKER_PORTS")

# Download MySql JDBC driver jar for demo pipeline
mysql_jdbc_driver_url = "https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.23.tar.gz"

# Get environment variables
GMAIL_CRED = os.environ.get('GMAIL_CRED')

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
    deployment.engine_instances = ENGINE_INSTANCES
    # Add the deployment to SteamSets DataOps Platform, and start it
    sch.add_deployment(deployment)
    # deployment must be added before retrieving engine_version
    current_engine_version = deployment.engine_configuration.engine_version
    # retrieve deployment to make changes
    deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)

    # Fewer stage libs for quick deployment
    with open('partial_stage_libs.conf', 'r') as f:
        for rec in f:
            if rec.startswith('#'):
                continue
            deployment.engine_configuration.stage_libs.append(rec.rstrip())
    deployment.engine_configuration.stage_libs = [f"{lib}:{current_engine_version}" for lib in
                                                  deployment.engine_configuration.stage_libs]

    # # Full list of stage libs for complete deployment with all stages
    # with open('stage_libs.conf', 'r') as f:
    #     for rec in f:
    #         if rec.startswith('#'): continue
    #         deployment.engine_configuration.stage_libs.append(rec.rstrip())
    # deployment.engine_configuration.stage_libs = [f"{lib}:{current_engine_version}" for lib in
    #                                               deployment.engine_configuration.stage_libs]

    # get list of enterprise libs
    with open('enterprise_libs.conf', 'r') as f:
        for rec in f:
            if rec.startswith('#'):
                continue
            deployment.engine_configuration.stage_libs.append(rec.rstrip())

    # retrieve deployment configs
    sdc_properties = javaproperties.loads(
        deployment.engine_configuration.advanced_configuration.data_collector_configuration)

    # read SDC properties
    for key in config['SDC_PROPERTIES']:
        sdc_properties[key] = config['SDC_PROPERTIES'][key]

    # read runtime resources
    for key in config['RUNTIME_RESOURCES']:
        sdc_properties[key] = config['RUNTIME_RESOURCES'][key]

    if platform == "darwin":
        print("##### Mac Os Detected #####")
        sdc_properties['sdc.base.http.url'] = 'http://localhost:18630'

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties
    # verify persisted config changes
    # deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    # print(javaproperties.loads(deployment.engine_configuration.advanced_configuration.data_collector_configuration)[
    #           'production.maxBatchSize'])

    # Update external_resource_location
    expected_external_resource_location = '/var/resources/externalResources.tgz'
    deployment.engine_configuration.external_resource_location = expected_external_resource_location

    # Update JAVA OPTIONS
    java_config = deployment.engine_configuration.java_configuration
    java_config.java_memory_strategy = 'ABSOLUTE'
    java_config.maximum_java_heap_size_in_mb = MAX_HEAP
    java_config.minimum_java_heap_size_in_mb = MIN_HEAP
    with open('java_options.conf', 'r') as f:
        for rec in f:
            if rec.startswith('#'):
                continue
            java_config.java_options = f"{java_config.java_options} {rec.rstrip()}"

    # configure aws credential store
    cred_properties = javaproperties.loads(deployment.engine_configuration.advanced_configuration.credential_stores)
    config.read('deployment.conf')
    for key in config['CRED_STORE']:
        cred_properties[key] = config['CRED_STORE'][key]
    cred_properties = javaproperties.dumps(cred_properties)
    deployment.engine_configuration.advanced_configuration.credential_stores = cred_properties

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties
    # persist changes to the deployment
    sch.update_deployment(deployment)
    sch.start_deployment(deployment)
    if INSTALL_TYPE == "DOCKER":
        # engine version string to include in docker container name
        if 'http.port' in config['SDC_PROPERTIES']:
            engine_version = config['SDC_PROPERTIES']['http.port']
        else:
            engine_version = current_engine_version.replace(".", "")

        ports_list = DOCKER_PORTS.split(",")
        ports_list = [f"-p {port}:{port}" for port in ports_list]
        ports_string = ' '.join(str(port) for port in ports_list)
        if not ports_list:
            # run SDC container under Docker 'cluster' network + add a volume for MySql JDBC driver
            install_script = deployment.install_script().replace("docker run",
                                                                 f"docker run --network=cluster  -h sdc.cluster --name sdc-{engine_version} -e STREAMSETS_LIBRARIES_EXTRA_DIR=/opt/sdc-extras -v /home/ubuntu/JDBC/mysql-connector-java-8.0.23.jar:/opt/sdc-extras/streamsets-datacollector-jdbc-lib/lib/mysql-connector-java-8.0.23.jar:ro ")
        else:
            # run SDC container under Docker 'cluster' network + add a volume for MySql JDBC driver
            # expose some Docker ports
            install_script = deployment.install_script().replace("docker run",
                                                                 f"docker run --network=cluster  -h sdc.cluster --name sdc-{engine_version} {ports_string} -e STREAMSETS_LIBRARIES_EXTRA_DIR=/opt/sdc-extras -v /home/ubuntu/JDBC/mysql-connector-java-8.0.23.jar:/opt/sdc-extras/streamsets-datacollector-jdbc-lib/lib/mysql-connector-java-8.0.23.jar:ro ")

        with open("install_script.sh", "w") as f:
            f.write(install_script)
        # Download the MySql JDBC driver if not present under $HOME/JDBC
        with open("pre_install_script.sh", "w") as f:
            if not os.path.exists("$HOME/JDBC/mysql-connector-java-8.0.23.tar.gz"):
                f.write(
                    'wget https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.23.tar.gz -P $HOME/JDBC/\n')
                f.write('tar -xf $HOME/JDBC/mysql-connector-java-8.0.23.tar.gz -C $HOME/JDBC/\n')
                f.write('mv $HOME/JDBC/mysql-connector-java-8.0.23/mysql-connector-java-8.0.23.jar $HOME/JDBC/\n')
                f.write('echo "Finished running pre install tasks"')
        with open("install_script.sh", "w") as f:
            f.write('docker network create cluster\n')
            f.write(install_script)
        os.chmod("install_script.sh", stat.S_IRWXU)
        os.system("sh install_script.sh")
    if INSTALL_TYPE == "TARBALL":
        install_script = deployment.install_script().replace("--foreground", "--background")
        # defaults the download & install location
        install_script = f"{install_script} --no-prompt --download-dir=$HOME/.streamsets/download/dc " \
                         f"--install-dir=$HOME/.streamsets/install/dc "
        with open("install_script.sh", "w") as f:
            f.write('ulimit -n 32768\n')
            # if there's a requirement to pass in some java options during bootstrapping, set those via STREAMSETS_BOOTSTRAP_JAVA_OPTS.
            # f.write('export STREAMSETS_BOOTSTRAP_JAVA_OPTS="-Dhttps.proxyHost=<> -Dhttps.proxyPort=<> -Dhttp.proxyHost=<> -Dhttp.proxyPort=<> -Dhttp.nonProxyHosts=<>\n')
            f.write(install_script)
        os.chmod("install_script.sh", stat.S_IRWXU)
        os.system("sh install_script.sh")
        # Download/install the MySql JDBC driver if not present
        with open("post_install_script.sh", "w") as f:
            if not os.path.exists("./mysql-connector-java-8.0.23.tar.gz"):
                f.write('wget https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.23.tar.gz\n')
                f.write('tar -xf mysql-connector-java-8.0.23.tar.gz\n')
            f.write(
                f"mkdir -p $HOME/.streamsets/install/dc/streamsets-datacollector-{current_engine_version}/externalResources"
                f"/streamsets-libs-extras/streamsets-datacollector-jdbc-lib/lib/\n")
            f.write(f'cp ./mysql-connector-java-8.0.23/mysql-connector-java-8.0.23.jar '
                    f'$HOME/.streamsets/install/dc/streamsets-dataco'
                    f'llector-{current_engine_version}/externalResources/streamsets-libs-extras/streamsets-datacollector'
                    f'-jdbc-lib/lib/\n')
            f.write(
                f'sudo echo {GMAIL_CRED} > $HOME/.streamsets/install/dc/streamsets-datacollector-{current_engine_version}/etc/email-password.txt\n')
            f.write('echo "Finished running post install tasks"')
        os.chmod("post_install_script.sh", stat.S_IRWXU)
        os.system("sh post_install_script.sh")
        # restart engine after installing JDBC driver jar
        deployment_id = deployment.deployment_id
        os.system(
            f'curl -X POST https://na01.hub.streamsets.com/provisioning/rest/v1/csp/deployment/{deployment_id}/restartEngines?isStaleOnly=false -H "Content-Type:application/json" -H "X-Requested-By:curl" -H "X-SS-REST-CALL:true" -H "X-SS-App-Component-Id: {CRED_ID}" -H "X-SS-App-Auth-Token: {CRED_TOKEN}" -i\n')


def delete_deployment():
    try:
        # for simplification getting deployment by name, in practice we MUST use deployment ID
        deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
        current_engine_version = deployment.engine_configuration.engine_version
        if 'http.port' in config['SDC_PROPERTIES']:
            engine_version = config['SDC_PROPERTIES']['http.port']
        else:
            engine_version = current_engine_version.replace(".", "")
        sch.delete_deployment(deployment)
        print(f"Deployment {DEPLOYMENT_NAME} removed")
    except:
        print(f"Deployment {DEPLOYMENT_NAME} not found !!")
    try:
        # for simplification getting environment by name, in practice we MUST use environmentcd  ID
        environments = sch.environments.get(environment_name=ENVIRONMENT_NAME)
        sch.deactivate_environment(environments)
        sch.delete_environment(environments)
        print(f"Environment {ENVIRONMENT_NAME} deactivated/removed !!")
    except:
        print(f"Environment {ENVIRONMENT_NAME} not found !!")

    try:
        if INSTALL_TYPE == "TARBALL":
            with open("cleanup_script.sh", "w") as f:
                f.write(
                    f"pid=`ps aux | grep streamsets-datacollector-{current_engine_version} | grep DataCollectorMain | awk {{'print $2'}}`\n")
                f.write(f"kill -9 $pid\n")
                f.write('echo "Finished cleanup tasks"\n')
        if INSTALL_TYPE == "DOCKER":
            with open("cleanup_script.sh", "w") as f:
                f.write(f"docker rm -f sdc-{engine_version}\n")
                f.write('echo "Finished cleanup tasks"\n')
        os.chmod("cleanup_script.sh", stat.S_IRWXU)
        os.system("sh cleanup_script.sh")
    except:
        print("DataCollector not running !!")
    if os.path.exists("install_script.sh"):
        os.remove("install_script.sh")
    if os.path.exists("post_install_script.sh"):
        os.remove("post_install_script.sh")
    if os.path.exists("pre_install_script.sh"):
        os.remove("pre_install_script.sh")
    if os.path.exists("cleanup_script.sh"):
        os.remove("cleanup_script.sh")


def update_deployment():
    deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    current_engine_version = deployment.engine_configuration.engine_version
    # Update deployment name and tag/s
    deployment.deployment_name = DEPLOYMENT_NAME
    deployment.tags = [DEPLOYMENT_TAGS]

    # Fewer stage libs for quick deployment
    deployment.engine_configuration.stage_libs = []
    with open('partial_stage_libs.conf', 'r') as f:
        for rec in f:
            if rec.startswith('#'):
                continue
            deployment.engine_configuration.stage_libs.append(rec.rstrip())
    deployment.engine_configuration.stage_libs = [f"{lib}:{current_engine_version}" for lib in
                                                  deployment.engine_configuration.stage_libs]

    # # Full list of stage libs for complete deployment with all stages
    # with open('stage_libs.conf', 'r') as f:
    #     for rec in f:
    #         if rec.startswith('#'): continue
    #         deployment.engine_configuration.stage_libs.append(rec.rstrip())
    # deployment.engine_configuration.stage_libs = [f"{lib}:{current_engine_version}" for lib in
    #                                               deployment.engine_configuration.stage_libs]

    # get list of enterprise libs
    with open('enterprise_libs.conf', 'r') as f:
        for rec in f:
            if rec.startswith('#'):
                continue
            deployment.engine_configuration.stage_libs.append(rec.rstrip())

    # retrieve deployment configs
    sdc_properties = javaproperties.loads(
        deployment.engine_configuration.advanced_configuration.data_collector_configuration)

    # read SDC properties
    for key in config['SDC_PROPERTIES']:
        sdc_properties[key] = config['SDC_PROPERTIES'][key]

    # read runtime resources
    for key in config['RUNTIME_RESOURCES']:
        sdc_properties[key] = config['RUNTIME_RESOURCES'][key]

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties

    # Update JAVA OPTIONS
    java_config = deployment.engine_configuration.java_configuration
    # default is PERCENTAGE
    java_config.java_memory_strategy = 'ABSOLUTE'
    java_config.maximum_java_heap_size_in_mb = MIN_HEAP
    java_config.minimum_java_heap_size_in_mb = MAX_HEAP
    java_options = ""
    with open('java_options.conf', 'r') as f:
        for rec in f:
            if rec.startswith('#'):
                continue
            java_options = f"{java_options} {rec.rstrip()}"
        java_config.java_options = java_options

    # configure aws credential store
    cred_properties = javaproperties.loads(deployment.engine_configuration.advanced_configuration.credential_stores)
    config.read('deployment.conf')
    for key in config['CRED_STORE']:
        cred_properties[key] = config['CRED_STORE'][key]
    cred_properties = javaproperties.dumps(cred_properties)
    deployment.engine_configuration.advanced_configuration.credential_stores = cred_properties

    properties = javaproperties.dumps(sdc_properties)
    deployment.engine_configuration.advanced_configuration.data_collector_configuration = properties
    # persist changes to the deployment
    sch.update_deployment(deployment)
    sch.stop_deployment(deployment)
    sch.start_deployment(deployment)
    # restart engine after updating the deployment
    deployment_id = deployment.deployment_id
    os.system(
        f'curl -X POST https://na01.hub.streamsets.com/provisioning/rest/v1/csp/deployment/{deployment_id}/restartEngines?isStaleOnly=false -H "Content-Type:application/json" -H "X-Requested-By:curl" -H "X-SS-REST-CALL:true" -H "X-SS-App-Component-Id: {CRED_ID}" -H "X-SS-App-Auth-Token: {CRED_TOKEN}" -i\n')


if sch.deployments.contains(deployment_name=DEPLOYMENT_NAME):
    print(f"Deployment {DEPLOYMENT_NAME} already exists")
    while True:
        user_choice = input("Available Options:[delete/update/exit]: ")
        if user_choice in ['delete', 'update', 'exit']:
            break
    if user_choice == "delete":
        print(f"Deployment {DEPLOYMENT_NAME} will be deleted !!")
        delete_deployment()
    elif user_choice == "update":
        print(f"Deployment {DEPLOYMENT_NAME} will be updated !!")
        update_deployment()
    else:
        print("Goodbye !!")
else:
    create_deployment()
print("Time for completion: ", (time.time() - start_time), " secs")
