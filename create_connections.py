import json
import configparser
import time
import warnings
import csv, ast
# Import the ControlHub class from the SDK.
from streamsets.sdk import ControlHub
from streamsets.sdk.exceptions import ConnectionError
from streamsets.sdk import exceptions

start_time = time.time()
config = configparser.ConfigParser()
config.optionxform = lambda option: option

CREDENTIALS_PROPERTY_PATH = "./private/credentials.properties"
config.read(CREDENTIALS_PROPERTY_PATH)
CRED_ID = config.get("SECURITY", "CRED_ID")
CRED_TOKEN = config.get("SECURITY", "CRED_TOKEN")

warnings.simplefilter("ignore")
# Connect to the StreamSets DataOps Platform.
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)
# Retrieve the Data Collector engine to be used as the authoring engine
engine = sch.engines.get(engine_url='http://sdc.cluster:18512')

# Open and read the JSON file
json_file_path = "./resources/connections.json"
csv_file_path = "./resources/connections.csv"
with open(json_file_path, 'r') as file:
    data = json.load(file)  # Load JSON data from the file


def create_connection_from_json():
    try:
        for connection_details in data['connections']:
            # Build the Connection instance by passing a few key parameters into the build method
            connection_tags = ast.literal_eval(connection_details['tags'])
            # Instantiate the ConnectionBuilder instance
            connection_builder = sch.get_connection_builder()
            connection = connection_builder.build(title=connection_details['title'],
                                                  connection_type=connection_details['connection_type'],
                                                  authoring_data_collector=engine,
                                                  tags=connection_tags)

            # Set connection configuration
            # use the get_connection_configs() function to get connection_type and associated config names
            for connection_config in connection_details['configs']:
                connection.connection_definition.configuration[connection_config] = connection_details['configs'][
                    connection_config]
            try:
                sch.add_connection(connection)
                print(f"Connection with the name '{connection_details['title']}' created successfully.")
            except ConnectionError as e:
                # Catching the specific exception
                if 'CONNECTION_11' in str(e):
                    print(f"Error: A connection with the name '{connection_details['title']}' already exists.")
                else:
                    print(f"Connection error occurred: {e}")

    except exceptions as e:
        print(f"Connection error occurred: {e}")


def create_connection_from_csv():
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            connection_type = row['connection_type']
            title = row['title']
            tags = ast.literal_eval(row['tags'])  # Convert string to list
            configs = ast.literal_eval(row['configs'])  # Convert string to dictionary
            # Instantiate the ConnectionBuilder instance
            connection_builder = sch.get_connection_builder()
            # Build the Connection instance by passing a few key parameters into the build method
            connection = connection_builder.build(title=title,
                                                  connection_type=connection_type,
                                                  authoring_data_collector=engine,
                                                  tags=tags)
            # Set connection configuration
            # use the get_connection_configs() function to get connection_type and associated config names
            for config_name, config_value in configs.items():
                connection.connection_definition.configuration[config_name] = config_value
            try:
                sch.add_connection(connection)
                print(f"Connection with the name '{title}' created successfully.")
            except ConnectionError as e:
                # Catching the specific exception
                if 'CONNECTION_11' in str(e):
                    print(f"Error: A connection with the name '{title}' already exists.")
                else:
                    print(f"Connection error occurred: {e}")


# print config for a given connection type
def get_connection_configs(connection_name):
    try:
        connection_details = sch.connections.get(name=connection_name)
        # print(connection_details.connection_definition.configuration.items())
        print(f"Connection Type: {connection_details.connection_type}")
        print(
            f"Connection configs: {list(connection_details.connection_definition.configuration.__dict__['_id_to_remap'].values())}")
    except ValueError as e:
        print(f"Connection not found: {e}")


# convert JSON connection data to CSV format
def json_to_csv():
    # Convert the JSON data to CSV
    csv_data = []
    header = ['connection_type', 'title', 'tags', 'configs']

    # Flattening the JSON data
    for conn in data['connections']:
        flattened_conn = {
            'connection_type': conn['connection_type'],
            'title': conn['title'],
            'tags': conn['tags'],
            'configs': conn['configs']
        }
        csv_data.append(flattened_conn)

    # Writing to CSV file
    csv_file = '/Users/sanju/workspace/toolkit/resources/connections.csv'
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        for row in csv_data:
            writer.writerow({
                'connection_type': row['connection_type'],
                'title': row['title'],
                'tags': row['tags'],
                'configs': row['configs']
            })


def delete_connections():
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            title = row['title']
            connection = sch.connections.get(name=title)
            sch.delete_connection(connection)


# get_connection_configs('sanju_s3_with_accessKeys')
# create_connection()
# json_to_csv()
# create_connection_from_csv()
delete_connections()
# create_connection_from_json()

print("Time for completion: ", (time.time() - start_time), " secs")
