import configparser
import os
import subprocess
import time
import warnings
import javaproperties
import pyfiglet

from deployment_logger import Logger
from controlhub_manager import ControlHubManager

warnings.simplefilter("ignore")
DEPLOYMENT_CONFIG = 'config/common/deployment.conf'
JAVA_OPTS = 'config/common/java_options.conf'
SDC_STAGE_LIBS = 'config/sdc/sdc_partial_stage_libs.conf'
TRANSFORMER_STAGE_LIBS = 'config/transformer/transformer_partial_stage_libs.conf'
INSTALLATION_HOME = os.getenv("HOME")
TARBALL_DOWNLOAD_PATH_SDC = '.streamsets/download/dc'
TARBALL_DOWNLOAD_PATH_TRANSFORMER = '.streamsets/download/transformer'
TARBALL_INSTALLATION_PATH_SDC = '.streamsets/install/dc'
TARBALL_INSTALLATION_PATH_TRANSFORMER = '.streamsets/install/transformer'
SCH_BASE_URL = 'https://na01.hub.streamsets.com'
SCRIPT_TIMEOUT = 300
TRANSFORMER_DOCKER_PREFIX = 'tf-'
SDC_DOCKER_PREFIX = 'sdc-'


class DeploymentManager:
    def __init__(self):
        self.start_time = time.time()
        self.logger = Logger()
        self.control_hub = ControlHubManager().controlHub_login()
        self.config = configparser.ConfigParser()
        self.config.optionxform = lambda option: option
        self.read_deployment_configs()
        print(pyfiglet.Figlet(font='big', width=80).renderText('StreamSets Ops'))

    def read_deployment_configs(self):
        if DEPLOYMENT_CONFIG:
            try:
                # Load deployment configs
                self.config.read(DEPLOYMENT_CONFIG)
                # Set attributes from deployment configurations
                for section in self.config.sections():
                    for key in self.config[section]:
                        setattr(self, key, self.config.get(section, key))

            except (configparser.NoSectionError, configparser.NoOptionError, FileNotFoundError) as e:
                self.logger.log_msg('error', f"Error reading deployment configurations: {e}")

        else:
            raise ValueError("DEPLOYMENT_CONFIG is not set or deployment configuration file is missing.")

    def create_deployment(self):
        try:
            # Instantiate an EnvironmentBuilder instance to build an environment, and activate it.
            environment_builder = self.control_hub.get_environment_builder(
                environment_type=self.config.get("DEPLOYMENT", "ENVIRONMENT_TYPE"))
            environment = environment_builder.build(
                environment_name=self.config.get("DEPLOYMENT", "ENVIRONMENT_NAME"),
                environment_type=self.config.get("DEPLOYMENT", "ENVIRONMENT_TYPE"),
                environment_tags=[f'{self.config.get("DEPLOYMENT", "ENVIRONMENT_TAGS")}'],
                allow_nightly_engine_builds=False)

            # Add the environment and activate it
            self.control_hub.add_environment(environment)
            self.control_hub.activate_environment(environment)

            # Instantiate the DeploymentBuilder instance to build the deployment
            deployment_builder = self.control_hub.get_deployment_builder(
                deployment_type=self.config.get("DEPLOYMENT", "DEPLOYMENT_TYPE"))

            # Build the deployment and specify the Sample Environment created previously.
            deployment = deployment_builder.build(
                deployment_name=self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME"),
                deployment_type=self.config.get("DEPLOYMENT", "DEPLOYMENT_TYPE"),
                environment=environment,
                engine_type=self.config.get("DEPLOYMENT", "ENGINE_TYPE"),
                engine_version=self.config.get("DEPLOYMENT", "ENGINE_VERSION"),
                deployment_tags=[f'{self.config.get("DEPLOYMENT", "DEPLOYMENT_TAGS")}'])

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                deployment = deployment_builder.build(
                    deployment_name=self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME"),
                    deployment_type=self.config.get("DEPLOYMENT", "DEPLOYMENT_TYPE"),
                    environment=environment,
                    engine_type=self.config.get("DEPLOYMENT", "ENGINE_TYPE"),
                    engine_version=self.config.get("DEPLOYMENT", "ENGINE_VERSION"),
                    scala_binary_version=self.config.get("DEPLOYMENT", "SCALA_VERSION"),
                    deployment_tags=[f'{self.config.get("DEPLOYMENT", "DEPLOYMENT_TAGS")}'])

            # Set engine labels
            labels = self.config.get("DEPLOYMENT", "ENGINE_LABELS").split(",")
            deployment.engine_configuration.engine_labels = labels

            # Deployment type (Docker/Tarball)
            deployment.install_type = self.config.get("DEPLOYMENT", "INSTALL_TYPE")
            deployment.engine_instances = self.config.get("DEPLOYMENT", "ENGINE_INSTANCES")

            # Add the deployment to StreamSets DataOps Platform, and start it
            self.control_hub.add_deployment(deployment)

            # Retrieve deployment to make changes
            current_engine_version = deployment.engine_configuration.engine_version
            deployment = self.control_hub.deployments.get(
                deployment_name=self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME"))

            # Save IDs for cleanup
            update_config = configparser.ConfigParser()
            update_config.optionxform = lambda option: option
            update_config.read(DEPLOYMENT_CONFIG)
            update_config['DEPLOYMENT']['DEPLOYMENT_ID'] = str(deployment.deployment_id)
            update_config['DEPLOYMENT']['ENVIRONMENT_ID'] = str(environment.environment_id)

            with open(DEPLOYMENT_CONFIG, 'w') as configfile:
                update_config.write(configfile)

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                # Retrieve deployment configs
                engine_properties = javaproperties.loads(
                    deployment.engine_configuration.advanced_configuration.data_collector_configuration)

                # Fewer stage libs for quick deployment
                try:
                    with open(SDC_STAGE_LIBS, 'r') as f:
                        for rec in f:
                            if rec.startswith('#'):
                                continue
                            deployment.engine_configuration.stage_libs.append(rec.rstrip())
                    deployment.engine_configuration.stage_libs = [
                        f"{lib}:{current_engine_version}" for lib in deployment.engine_configuration.stage_libs]
                except Exception as e:
                    self.logger.log_msg('error', f"Error reading SDC stage libs: {e}")

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                engine_properties = javaproperties.loads(
                    deployment.engine_configuration.advanced_configuration.transformer_configuration)

                # Fewer stage libs for quick deployment
                try:
                    with open(TRANSFORMER_STAGE_LIBS, 'r') as f:
                        for rec in f:
                            if rec.startswith('#'):
                                continue
                            deployment.engine_configuration.stage_libs.append(rec.rstrip())
                    deployment.engine_configuration.stage_libs = [
                        f"{lib}:{current_engine_version}" for lib in deployment.engine_configuration.stage_libs]
                except Exception as e:
                    self.logger.log_msg('error', f"Error reading Transformer stage libs: {e}")

            # Read engine properties
            for key in self.config['ENGINE_PROPERTIES']:
                engine_properties[key] = self.config['ENGINE_PROPERTIES'][key]

            # Read runtime resources
            if 'RUNTIME_RESOURCES' in self.config:
                for key in self.config['RUNTIME_RESOURCES']:
                    engine_properties[key] = self.config['RUNTIME_RESOURCES'][key]

            engine_configurations = javaproperties.dumps(engine_properties)

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                deployment.engine_configuration.advanced_configuration.data_collector_configuration = engine_configurations

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                deployment.engine_configuration.advanced_configuration.transformer_configuration = engine_configurations

            # Update external_resource_location
            if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "DOCKER":
                deployment.engine_configuration.external_resource_source = self.config.get("DEPLOYMENT",
                                                                                           "EXTERNAL_RESOURCES_PATH_DOCKER")

            if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "TARBALL":
                deployment.engine_configuration.external_resource_source = self.config.get("DEPLOYMENT",
                                                                                           "EXTERNAL_RESOURCES_PATH_TARBALL")

            # Update JAVA OPTIONS
            java_config = deployment.engine_configuration.java_configuration
            java_config.java_memory_strategy = 'ABSOLUTE'
            java_config.maximum_java_heap_size_in_mb = self.config.get("DEPLOYMENT", "MAX_HEAP")
            java_config.minimum_java_heap_size_in_mb = self.config.get("DEPLOYMENT", "MIN_HEAP")

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                try:
                    with open(JAVA_OPTS, 'r') as f:
                        for rec in f:
                            if rec.startswith('#'):
                                continue
                            java_config.java_options = f"{java_config.java_options} {rec.rstrip()}"
                except Exception as e:
                    self.logger.log_msg('error', f"Error reading JAVA options: {e}")

            # Configure AWS credential store
            cred_properties = javaproperties.loads(
                deployment.engine_configuration.advanced_configuration.credential_stores)
            if 'CRED_STORE' in self.config:
                for key in self.config['CRED_STORE']:
                    cred_properties[key] = self.config['CRED_STORE'][key]

            cred_properties = javaproperties.dumps(cred_properties)
            deployment.engine_configuration.advanced_configuration.credential_stores = cred_properties

            engine_configurations = javaproperties.dumps(engine_properties)

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                deployment.engine_configuration.advanced_configuration.data_collector_configuration = engine_configurations

            if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                deployment.engine_configuration.advanced_configuration.transformer_configuration = engine_configurations

            # Persist changes to the deployment
            self.control_hub.update_deployment(deployment)
            self.control_hub.start_deployment(deployment)

            # Handle Docker installation
            if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "DOCKER":
                if 'http.port' in self.config['ENGINE_PROPERTIES']:
                    engine_version = self.config['ENGINE_PROPERTIES']['http.port']
                else:
                    engine_version = current_engine_version.replace(".", "")

                ports_list = self.config.get("DEPLOYMENT", "DOCKER_PORTS").split(",")
                ports_list = [f"-p {port}:{port}" for port in ports_list]
                ports_string = ' '.join(str(port) for port in ports_list)

                try:
                    if not ports_list:
                        # Run SDC container under Docker 'DOCKER_NETWORK' network
                        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                            install_script = deployment.install_script().replace("docker run",
                                                                                 f"docker run --network={self.config.get('DEPLOYMENT', 'DOCKER_NETWORK')} -h sdc.cluster --name {SDC_DOCKER_PREFIX}{engine_version} ")
                        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                            install_script = deployment.install_script().replace("docker run",
                                                                                 f"docker run --network={self.config.get('DEPLOYMENT', 'DOCKER_NETWORK')} -h transformer.cluster --name {TRANSFORMER_DOCKER_PREFIX}{engine_version} ")
                    else:
                        # Run SDC container under Docker 'DOCKER_NETWORK' network + expose some Docker ports listed via DOCKER_PORTS
                        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                            install_script = deployment.install_script().replace("docker run",
                                                                                 f"docker run --network={self.config.get('DEPLOYMENT', 'DOCKER_NETWORK')} -h sdc.cluster --name {SDC_DOCKER_PREFIX}{engine_version} {ports_string} ")
                        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                            install_script = deployment.install_script().replace("docker run",
                                                                                 f"docker run --network={self.config.get('DEPLOYMENT', 'DOCKER_NETWORK')} -h transformer.cluster --name {TRANSFORMER_DOCKER_PREFIX}{engine_version} {ports_string} ")
                    try:
                        # Attempt to create the DOCKER_NETWORK
                        subprocess.run(
                            ["docker", "network", "create", f"{self.config.get('DEPLOYMENT', 'DOCKER_NETWORK')}"],
                            check=True, text=True, capture_output=True)
                    except subprocess.CalledProcessError as e:
                        # Check if the network already exists
                        if "network with name cluster already exists" in e.stderr:
                            self.logger.log_msg('info', "Network 'cluster' already exists, continuing...")
                        else:
                            # For any other error, re-raise the exception
                            raise
                    try:
                        # run docker run command for the engine
                        self.logger.log_msg('info', f"Docker Command: {install_script}")
                        subprocess.run(install_script, check=True, capture_output=True, text=True, shell=True)
                        self.logger.log_msg('info', "Deployment completed successfully.")
                        # Log the time for completion
                        self.logger.log_msg('info', f"Time for completion: {time.time() - self.start_time:.2f} secs")
                    except subprocess.CalledProcessError as e:
                        self.logger.log_msg('error', f"Engine set-up encountered error: {e.stderr}")
                except Exception as e:
                    self.logger.log_msg('error', f"Engine install failed: {e}")

            # Handle TARBALL installation
            if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "TARBALL":
                install_script = deployment.install_script(install_mechanism='BACKGROUND')
                if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                    # create download and install directories
                    os.makedirs(f"{INSTALLATION_HOME}/{TARBALL_DOWNLOAD_PATH_SDC}", exist_ok=True)
                    os.makedirs(f"{INSTALLATION_HOME}/{TARBALL_INSTALLATION_PATH_SDC}", exist_ok=True)
                    # add download/install path to the installation script
                    install_script = f"{install_script} --no-prompt --download-dir=$HOME/{TARBALL_DOWNLOAD_PATH_SDC} " \
                                     f"--install-dir=$HOME/{TARBALL_INSTALLATION_PATH_SDC}"
                if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                    # create download and install directories
                    os.makedirs(f"{INSTALLATION_HOME}/{TARBALL_DOWNLOAD_PATH_SDC}", exist_ok=True)
                    os.makedirs(f"{INSTALLATION_HOME}/{TARBALL_INSTALLATION_PATH_TRANSFORMER}", exist_ok=True)
                    # add download/install path to the installation script
                    install_script = f"{install_script} --no-prompt --download-dir=$HOME/{TARBALL_DOWNLOAD_PATH_TRANSFORMER} " \
                                     f"--install-dir=$HOME/{TARBALL_INSTALLATION_PATH_TRANSFORMER}"
                try:
                    # run install script for tarball install
                    # ulimit -n 32768
                    subprocess.run(install_script, check=True, shell=True, timeout=SCRIPT_TIMEOUT)
                    self.logger.log_msg('info', "Deployment completed successfully.")
                    # Log the time for completion
                    self.logger.log_msg('info', f"Time for completion: {time.time() - self.start_time:.2f} secs")
                except subprocess.TimeoutExpired:
                    self.logger.log_msg('error', "The install script took too long to complete and was terminated.")
                except subprocess.CalledProcessError as e:
                    self.logger.log_msg('error', f"Engine install failed: {e.stderr}")

        except Exception as e:
            self.logger.log_msg('error', f"An error occurred during deployment creation: {e.stderr}")

    def delete_deployment(self):
        try:
            # retrieve id's from the deployment.conf written during creation
            environment_id = self.config.get("DEPLOYMENT", "ENVIRONMENT_ID")
            deployment_id = self.config.get("DEPLOYMENT", "DEPLOYMENT_ID")
            deployment = self.control_hub.deployments.get(deployment_id=deployment_id)
            current_engine_version = deployment.engine_configuration.engine_version
            if 'http.port' in self.config['ENGINE_PROPERTIES']:
                engine_version = self.config['ENGINE_PROPERTIES']['http.port']
            else:
                engine_version = current_engine_version.replace(".", "")
            self.control_hub.delete_deployment(deployment)
            self.logger.log_msg('info',
                                f"Deployment {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} removed ")
        except:
            self.logger.log_msg('warning',
                                f"Deployment {self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME")} not found !!")
        try:
            environment = self.control_hub.environments.get(environment_id=environment_id)
            self.control_hub.deactivate_environment(environment)
            self.control_hub.delete_environment(environment)
            self.logger.log_msg('info',
                                f"Environment {self.config.get("DEPLOYMENT", "ENVIRONMENT_NAME")} deactivated/removed !!")

        except:
            self.logger.log_msg('warning',
                                f"Environment {self.config.get("DEPLOYMENT", "ENVIRONMENT_NAME")} not found !!")

        try:
            # TARBALL cleanup
            if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "TARBALL":
                if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                    installation_dir = f"{INSTALLATION_HOME}/{TARBALL_INSTALLATION_PATH_TRANSFORMER}/streamsets-transformer_{self.config.get("DEPLOYMENT", "SCALA_VERSION")}-{self.config.get("DEPLOYMENT", "ENGINE_VERSION")}"
                    try:
                        subprocess.run(f"rm -rf {installation_dir}", check=True, shell=True)
                        self.logger.log_msg('info', "Finished cleanup tasks !!")
                        self.logger.log_msg('info', "Environment/Deployment deleted successfully.")

                    except subprocess.CalledProcessError as e:
                        self.logger.log_msg('info', f"Engine clean-up encountered error: {e.stderr} ")

                if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                    installation_dir = f"{INSTALLATION_HOME}/{TARBALL_INSTALLATION_PATH_SDC}/streamsets-datacollector-{self.config.get("DEPLOYMENT", "ENGINE_VERSION")}"
                    try:
                        subprocess.run(f"rm -rf {installation_dir}", check=True, shell=True)
                        self.logger.log_msg('info', "Finished cleanup tasks !!")
                        self.logger.log_msg('info', "Environment/Deployment deleted successfully.")

                    except subprocess.CalledProcessError as e:
                        self.logger.log_msg('info', f"Engine clean-up encountered error: {e.stderr} ")

            # DOCKER cleanup
            if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "DOCKER":
                if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
                    cleanup_command = f"docker rm -f {TRANSFORMER_DOCKER_PREFIX}{engine_version}\n"
                if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
                    cleanup_command = f"docker rm -f {SDC_DOCKER_PREFIX}{engine_version}\n"
                try:
                    subprocess.run(cleanup_command, capture_output=True, text=True, check=True, shell=True)
                    self.logger.log_msg('info', "Finished cleanup tasks !!")
                    self.logger.log_msg('info', "Environment/Deployment deleted successfully.")
                    # Log the time for completion
                    self.logger.log_msg('info', f"Time for completion: {time.time() - self.start_time:.2f} secs")
                except subprocess.CalledProcessError as e:
                    self.logger.log_msg('info', f"Engine clean-up encountered error: {e.stderr} ")

        except Exception as e:
            self.logger.log_msg('error', f"Deployment/Environment deletion encountered problems: {e}")

    def update_deployment(self):
        deployment = self.control_hub.deployments.get(deployment_name=self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME"))
        current_engine_version = deployment.engine_configuration.engine_version
        # Update deployment name and tag/s
        deployment.deployment_name = self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME")
        deployment.tags = [self.config.get("DEPLOYMENT", "DEPLOYMENT_TAGS")]
        # Update engine labels
        labels = self.config.get("DEPLOYMENT", "ENGINE_LABELS").split(",")
        deployment.engine_configuration.engine_labels = labels

        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
            with open(SDC_STAGE_LIBS, 'r') as f:
                for rec in f:
                    if rec.startswith('#'):
                        continue
                    deployment.engine_configuration.stage_libs.append(rec.rstrip())
            deployment.engine_configuration.stage_libs = [f"{lib}:{current_engine_version}" for lib in
                                                          deployment.engine_configuration.stage_libs]

            # retrieve deployment configs
            engine_properties = javaproperties.loads(
                deployment.engine_configuration.advanced_configuration.data_collector_configuration)
        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
            engine_properties = javaproperties.loads(
                deployment.engine_configuration.advanced_configuration.transformer_configuration)
            with open(TRANSFORMER_STAGE_LIBS, 'r') as f:
                for rec in f:
                    if rec.startswith('#'):
                        continue
                    deployment.engine_configuration.stage_libs.append(rec.rstrip())
            deployment.engine_configuration.stage_libs = [f"{lib}:{current_engine_version}" for lib in
                                                          deployment.engine_configuration.stage_libs]

        # read engine properties
        for key in self.config['ENGINE_PROPERTIES']:
            engine_properties[key] = self.config['ENGINE_PROPERTIES'][key]

        # read runtime resources
        if 'RUNTIME_RESOURCES' in self.config:
            for key in self.config['RUNTIME_RESOURCES']:
                engine_properties[key] = self.config['RUNTIME_RESOURCES'][key]

        engine_configurations = javaproperties.dumps(engine_properties)
        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
            deployment.engine_configuration.advanced_configuration.data_collector_configuration = engine_configurations
        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
            deployment.engine_configuration.advanced_configuration.transformer_configuration = engine_configurations
        # verify persisted config changes
        # deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
        # print(javaproperties.loads(deployment.engine_configuration.advanced_configuration.data_collector_configuration)[
        #           'production.maxBatchSize'])

        # Update external_resource_location
        if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "DOCKER":
            deployment.engine_configuration.external_resource_source = self.config.get("DEPLOYMENT",
                                                                                       "EXTERNAL_RESOURCES_PATH_DOCKER")
        if self.config.get("DEPLOYMENT", "INSTALL_TYPE") == "TARBALL":
            deployment.engine_configuration.external_resource_source = self.config.get("DEPLOYMENT",
                                                                                       "EXTERNAL_RESOURCES_PATH_TARBALL")

        # Update JAVA OPTIONS
        java_config = deployment.engine_configuration.java_configuration
        java_config.java_memory_strategy = 'ABSOLUTE'
        java_config.minimum_java_heap_size_in_mb = self.config.get("DEPLOYMENT", "MIN_HEAP")
        java_config.maximum_java_heap_size_in_mb = self.config.get("DEPLOYMENT", "MAX_HEAP")

        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
            # read existing java opts
            existing_options = set(java_config.java_options.split())
            with open(JAVA_OPTS, 'r') as f:
                for rec in f:
                    if rec.startswith('#'):
                        continue
                    option = rec.rstrip()
                    # Only add if it's not already present
                    if option not in existing_options:
                        existing_options.add(option)

            # Join the options back into a single string
            java_config.java_options = ' '.join(existing_options)

        # configure aws credential store
        cred_properties = javaproperties.loads(deployment.engine_configuration.advanced_configuration.credential_stores)
        self.config.read(DEPLOYMENT_CONFIG)
        if 'CRED_STORE' in self.config:
            for key in self.config['CRED_STORE']:
                cred_properties[key] = self.config['CRED_STORE'][key]
            cred_properties = javaproperties.dumps(cred_properties)
            deployment.engine_configuration.advanced_configuration.credential_stores = cred_properties

        engine_configurations = javaproperties.dumps(engine_properties)
        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'DC':
            deployment.engine_configuration.advanced_configuration.data_collector_configuration = engine_configurations
        if self.config.get("DEPLOYMENT", "ENGINE_TYPE") == 'TF':
            deployment.engine_configuration.advanced_configuration.transformer_configuration = engine_configurations

        # persist changes to the deployment
        self.control_hub.update_deployment(deployment)
        deployment_id = deployment.deployment_id
        control_hub = ControlHubManager()
        control_hub.controlHub_login()
        # restart engine after updating the deployment
        restart_engine_command = f'curl -X POST {SCH_BASE_URL}/provisioning/rest/v1/csp/deployment/{deployment_id}/restartEngines?isStaleOnly=false -H "Content-Type:application/json" -H "X-Requested-By:curl" -H "X-SS-REST-CALL:true" -H "X-SS-App-Component-Id: {control_hub.cred_id}" -H "X-SS-App-Auth-Token: {control_hub.cred_token}" -i'
        try:
            subprocess.run(restart_engine_command, capture_output=True, text=True, check=True, shell=True)
            self.logger.log_msg('info', "Environment/Deployment updated successfully.")
            # Log the time for completion
            self.logger.log_msg('info', f"Time for completion: {time.time() - self.start_time:.2f} secs")

        except subprocess.CalledProcessError as e:
            self.logger.log_msg('info', f"Engine restart encountered error: {e.stderr} ")

    def cleanup_deployment_scripts(self):
        cleanup_files = [
            "install_script.sh",
            "post_install_script.sh",
            "pre_install_script.sh",
            "cleanup_script.sh"
        ]
        for file in cleanup_files:
            if os.path.exists(file):
                os.remove(file)
        self.logger.log_msg('info', "Deployment scripts removed")

    def run(self):
        options = {
            '1': 'create',
            '2': 'update',
            '3': 'delete',
            '4': 'exit'
        }
        while True:
            print("Available StreamSets Deployment Options:")
            for key, value in options.items():
                print(f"{key}: {value}")

            user_choice = input("Choose an option by number or name: ").strip()
            if user_choice in options:
                user_choice = options[user_choice]

            if user_choice in options.values():
                break

        if user_choice == "create":
            if self.control_hub.deployments.contains(
                    deployment_name=self.config.get("DEPLOYMENT", "DEPLOYMENT_NAME")):
                self.logger.log_msg('warning',
                                    f"Deployment [ {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} ] already exists")
                self.logger.log_msg('warning',
                                    f"If you proceed, deployment [ {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} ] & environment [ {self.config.get('DEPLOYMENT', 'ENVIRONMENT_NAME')} ] will first be terminated ")
                options = {
                    '1': 'proceed',
                    '2': 'exit'
                }
                while True:
                    print("Available Options:")
                    for key, value in options.items():
                        print(f"{key}: {value}")

                    user_choice = input("Choose an option by number or name: ").strip()
                    if user_choice in options:
                        user_choice = options[user_choice]

                    if user_choice in options.values():
                        break

                if user_choice == "proceed":
                    self.logger.log_msg('info',
                                        f"Deleting the deployment [ {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} ]")
                    self.delete_deployment()
                    self.create_deployment()
                else:
                    self.logger.log_msg('info', "Goodbye!!")
            else:
                self.create_deployment()

        elif user_choice == "update":
            self.logger.log_msg('info',
                                f"Updating deployment [ {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} ] ...")
            self.update_deployment()
        elif user_choice == "delete":
            self.logger.log_msg('warning',
                                f"Deployment [ {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} ] will be deleted!!")
            self.logger.log_msg('warning',
                                f"Environment [ {self.config.get('DEPLOYMENT', 'ENVIRONMENT_NAME')} ] will be deleted!!")
            options = {
                '1': 'proceed',
                '2': 'exit'
            }
            while True:
                print("Available Options:")
                for key, value in options.items():
                    print(f"{key}: {value}")

                user_choice = input("Choose an option by number or name: ").strip()
                if user_choice in options:
                    user_choice = options[user_choice]

                if user_choice in options.values():
                    break

            if user_choice == "proceed":
                self.logger.log_msg('info',
                                    f"Deleting the deployment [ {self.config.get('DEPLOYMENT', 'DEPLOYMENT_NAME')} ]")
                self.delete_deployment()
            else:
                self.logger.log_msg('info', "Goodbye!!")
        else:
            self.logger.log_msg('info', "Goodbye!!")


if __name__ == "__main__":
    manager = DeploymentManager()
    manager.run()
