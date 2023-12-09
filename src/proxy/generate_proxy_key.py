import boto3
from dotenv import load_dotenv
from os import path
import sys
sys.path.append(path.join(path.dirname(__file__), '..'))
import utils
import os
import subprocess

KEY_DIR = 'src/proxy'
KEY_NAME = 'proxy_key'
SSH_KEY = 'final_project_gen_key.pem'
DEPLOYMENT_FILE = 'fake_deployment_cluster.yml'
CLUSTER_NAME = 'sql_cluster'

if __name__ == '__main__':
    print('Generating proxy configuration file...')
    
    load_dotenv()
    session = boto3.session.Session(
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key'),
        aws_session_token=os.getenv('aws_session_token'),
        region_name='us-east-1',
    )
    client = session.client('ec2')

    instance_ids = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name=CLUSTER_NAME,
    )

    instance_descriptions = utils.describe_instances(
        client=client,
        instance_ids=instance_ids,
    )['Reservations'][0]['Instances']

    sql_cluster_hosts = [
        description['PublicDnsName'] for description in instance_descriptions
    ]

    key_file = utils.create_key(
        key_name=KEY_NAME,
        key_dir=KEY_DIR,
    )

    pub_key = utils.get_pub_key(key_file=key_file)
    
    utils.add_key_to_instances(
        pub_key=pub_key,
        hosts=sql_cluster_hosts,
        key_path=SSH_KEY
    )
