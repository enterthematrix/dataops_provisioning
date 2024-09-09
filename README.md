# Provisioning DataOps environment

### Pre-requisites
1. [Install](https://docs.streamsets.com/platform-sdk/learn/installation.html) StreamSets SDK for Python 
2. Create the following configuration files:

credentials.properties:
```
[DEFAULT]

[SECURITY]
CRED_ID=<SCH CRED_ID>
CRED_TOKEN=<SCH CRED_TOKEN>
```
3. Update config files under config dir as per requirements
4. Usage: ```python main.py  ``` to create/update/delete DataOps deployment



