import configparser
import warnings
import time

# Import the ControlHub class from the SDK.
from streamsets.sdk import ControlHub

# sys.path.insert(1, os.path.abspath('/Users/sanjeev/SDK_4x'))

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

deployment = sch.deployments.get(deployment_name=DEPLOYMENT_NAME)
print(f"Successfully created {DEPLOYMENT_NAME} deployment")