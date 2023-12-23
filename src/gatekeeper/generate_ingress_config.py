from os import path
import sys
sys.path.append(path.join(path.dirname(__file__), '..'))
import utils
from dotenv import load_dotenv
import boto3
import os
import json

FORBIDEN_CMDS = [
    'DROP DATABASE',
]

BODY_FIELDS = {
    '/mode': ['mode'],
    '/query': ['query']
}

DEPLOYMENT_FILE = 'deployment.yml'
CLUSTER_NAME = 'gatekeeper-trusted-host'
CONFIG_FILE_PATH = 'src/gatekeeper/config.json'

def generate_gatekeeper_ingress_config(client):
    print('Generating gatekeepr ingress configuration file...')
    instance_id = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name=CLUSTER_NAME,
    )[0]

    trusted_host_desc = utils.describe_instances(
        client=client,
        instance_ids=[instance_id],
    )['Reservations'][0]['Instances'][0]

    config = {
        'trustedHostname': trusted_host_desc['PrivateDnsName'],
        'forbidenCommands': FORBIDEN_CMDS,
        'bodyFields': BODY_FIELDS,
    }

    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    
if __name__ == '__main__':
    load_dotenv()
    session = boto3.session.Session(
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key'),
        aws_session_token=os.getenv('aws_session_token'),
        region_name='us-east-1',
    )
    client = session.client('ec2')
    generate_gatekeeper_ingress_config(client=client)
