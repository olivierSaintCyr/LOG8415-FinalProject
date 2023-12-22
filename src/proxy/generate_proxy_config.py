from os import path
import sys
sys.path.append(path.join(path.dirname(__file__), '..'))

import utils
from dotenv import load_dotenv
import os
import boto3
from start_sql_cluster import get_sql_cluster_node_role
import json

def node_sql_roles_to_proxy_config(node_roles: dict):
    return {
        'sqlClusterHostnames': {
            'master': node_roles['master']['PrivateDnsName'],
            'dataNodes': [
                data_node_info['PrivateDnsName'] for data_node_info in node_roles['data_nodes']
            ]
        } 
    }

def generate_proxy_config_file(node_roles: dict, config_file: str):
    proxy_config = node_sql_roles_to_proxy_config(node_roles)
    with open(config_file, 'w') as f:
        json.dump(proxy_config, f, indent=4)

DEPLOYMENT_FILE = 'fake_deployment_cluster.yml'
CLUSTER_NAME = 'sql_cluster'
PROXY_CONFIG_PATH = 'src/proxy/config.json'

def generate_proxy_config(client):
    print('Generating proxy configuration file...')
    
    

    instance_ids = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name=CLUSTER_NAME,
    )

    instance_descriptions = utils.describe_instances(
        client=client,
        instance_ids=instance_ids,
    )['Reservations'][0]['Instances']

    instance_network_infos = [
        {
            'PrivateDnsName': description['PrivateDnsName'],
        } for description in instance_descriptions
    ]

    instance_sql_roles = get_sql_cluster_node_role(
        net_info=instance_network_infos
    )

    generate_proxy_config_file(
        node_roles=instance_sql_roles,
        config_file=PROXY_CONFIG_PATH,
    )

    print('Proxy configuration file done!')

if __name__ == '__main__':
    load_dotenv()
    session = boto3.session.Session(
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key'),
        aws_session_token=os.getenv('aws_session_token'),
        region_name='us-east-1',
    )
    client = session.client('ec2')
    generate_proxy_config(client=client)
    