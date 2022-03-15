# Provisioning DataOps environment

### Pre-requisites
1. [Install](https://docs.streamsets.com/platform-sdk/learn/installation.html) StreamSets SDK for Python 
2. create a dataops.properties file with following params:
   ```
   [DEFAULT]
   CRED_ID=<DataOps API Cred ID>
   CRED_TOKEN=<DataOps API Cred Token>
   ENVIRONMENT_NAME=<>
   DEPLOYMENT_NAME=<>
   ENVIRONMENT_TYPE=<>
   ENVIRONMENT_TAGS=<>
   DEPLOYMENT_TYPE=<>
   DEPLOYMENT_TAGS=<>
   ENGINE_TYPE=DC
   ENGINE_VERSION=<>
   INSTALL_TYPE=TARBALL
   SLACK_WEBHOOK=<Slack Webhook URL>
   EMAIL_ADDRESS=<email address for notifications> ```
3. ```Usage: python main.py ``` create environment/deployment/engine
4. ```Usage: python cleanup.py ``` remove environment/deployment/engine created in above steps


