import configparser
import os
import time
import warnings
from streamsets.sdk import ControlHub

from deployment_logger import Logger

warnings.simplefilter("ignore")
CREDENTIALS_PROPERTIES = 'private/credentials.properties'

class ControlHubManager:
    def __init__(self):
        self.start_time = time.time()
        self.logger = Logger()
        self.config = configparser.ConfigParser()
        self.config.optionxform = lambda option: option

    def load_credentials(self):
        if CREDENTIALS_PROPERTIES:
            try:
                # Load credentials from a properties file
                self.config.read(CREDENTIALS_PROPERTIES)
                self.cred_id = self.config.get("SECURITY", "CRED_ID")
                self.cred_token = self.config.get("SECURITY", "CRED_TOKEN")

            except (configparser.NoSectionError, configparser.NoOptionError, FileNotFoundError) as e:
                self.logger.log_msg('error', f"Error loading credentials from file: {e}")
                self.logger.log_msg('warning', f"Attempting to load credentials from env variable")
                # Try to load from environment variables if file loading fails
                try:
                    # Load credentials from environment variables
                    # INGESTHUB in the env name refers to the SCH Org
                    self.cred_id = os.environ.get('CRED_ID_INGESTHUB')
                    self.cred_token = os.environ.get('CRED_TOKEN_INGESTHUB')

                    # Check if credentials were loaded successfully
                    if not self.cred_id or not self.cred_token:
                        raise ValueError(
                            "Missing credentials. Ensure both CRED_ID_CS and CRED_TOKEN_CS are set in environment variables."
                        )

                except ValueError as e:
                    self.logger.log_msg('error', f"Environment variable error: {e}")
                    raise
                except Exception as e:
                    self.logger.log_msg('error', f"Unexpected error loading credentials from environment: {e}")
                    raise

        else:
            raise ValueError("CREDENTIALS_PROPERTIES is not set or credential file is missing.")

    def controlHub_login(self):
        try:
            self.load_credentials()
            control_hub = ControlHub(credential_id=self.cred_id, token=self.cred_token)
            return control_hub
        except Exception as e:
            self.logger.log_msg('error', f"Failed to initialize ControlHubManager: {e}")
            raise