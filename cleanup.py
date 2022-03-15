import configparser
import os
import warnings
import time

import config as config
import configs as configs
import javaproperties
import properties as properties
import requests
# Import the ControlHub class from the SDK.
from streamsets.sdk import ControlHub

# sys.path.insert(1, os.path.abspath('/Users/sanjeev/SDK_4x'))
from streamsets.sdk.sch_models import SelfManagedDeployment, SelfManagedEnvironment

config = configparser.ConfigParser()
config.read('dataops.properties')
ENVIRONMENT_NAME = config.get("DEFAULT", "ENVIRONMENT_NAME")
DEPLOYMENT_NAME = config.get("DEFAULT", "DEPLOYMENT_NAME")

CRED_ID = config.get("DEFAULT", "CRED_ID")
CRED_TOKEN = config.get("DEFAULT", "CRED_TOKEN")

start_time = time.time()
warnings.simplefilter("ignore")

# Connect to the StreamSets DataOps Platform.
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)


def delete_deployment():
    try:
        deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
        current_engine_version = deployment.engine_configuration.engine_version
        sch.delete_deployment(deployment)
        print(f"Deployment {DEPLOYMENT_NAME} removed")
    except:
        print(f"Deployment {DEPLOYMENT_NAME} not found !!")
    try:
        environments = sch.environments.get(environment_name=ENVIRONMENT_NAME)
        sch.deactivate_environment(environments)
        sch.delete_environment(environments)
        print(f"Environment {ENVIRONMENT_NAME} deactivated/removed !!")
    except:
        print(f"Environment {ENVIRONMENT_NAME} not found !!")

        if os.path.exists("install_script.sh"):
            os.remove("install_script.sh")
        if os.path.exists("post_install_script.sh"):
            os.remove("post_install_script.sh")
        pid = os.system("ps aux | grep streamsets-datacollector-4.4.0 | grep DataCollectorMain | awk {'print $2'}")
        os.system(f"kill -9 {pid}")



delete_deployment()
