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

ENVIRONMENT_NAME = 'Sanjeev_Nomura_SM'
DEPLOYMENT_NAME = 'Sanjeev_Nomura_TB'


config = configparser.ConfigParser()
config.read('dataops.properties')

CRED_ID = config.get("DEFAULT", "CRED_ID")
CRED_TOKEN = config.get("DEFAULT", "CRED_TOKEN")

start_time = time.time()
warnings.simplefilter("ignore")

# Connect to the StreamSets DataOps Platform.
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)


def delete_deployment():
    environments = sch.environments.get(environment_name=ENVIRONMENT_NAME)
    deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
    sch.delete_deployment(deployment)
    sch.deactivate_environment(environments)
    sch.delete_environment(environments)

    if os.path.exists("install_script.sh"):
        os.remove("install_script.sh")


delete_deployment()
