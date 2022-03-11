import configparser

from streamsets.sdk import ControlHub, DataCollector
from inflection import camelize

config = configparser.ConfigParser()
config.read('dataops.properties')

CRED_ID = config.get("DEFAULT", "CRED_ID")
CRED_TOKEN = config.get("DEFAULT", "CRED_TOKEN")

# Connect to the StreamSets DataOps Platform.
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)
#engine = DataCollector('http://localhost:18630', control_hub=sch)     # or Transformer(...)
sdc = sch.data_collectors.get(url='http://localhost:18630')
engine = sdc._instance

# Retrieve the stage configuration definitions:
definitions = engine.api_client.definitions()
# Get the stage name we're interested in finding the config for:
stage = sch.get_pipeline_builder().add_stage('com_streamsets_pipeline_stage_origin_datalake_gen1_DataLakeDSource')
stage_name = stage.stage_name
# Find the configDefinitions for that stage in the definitions:
for item in definitions['stages']:
    if item['name'] == stage_name:
        config_defs = item['configDefinitions']
    # Find the field that you're trying to set the config for:
    stage.configuration.items()                 # manually check each config item and find the one you want
    # Or
    #stage.configuration.get(....)               # using either 'conf.{}'.format(camelize('<config_name>', False) OR 'conf.dataFormatConfig.{}'.format(camelize('<config_name>', False)
    # Check the values available to the field in question
    for config in config_defs:
        if config['name'] == '<field_name_from_above_step>':
            print('{}: {}'.format(config['name'], config['model']['values']))

