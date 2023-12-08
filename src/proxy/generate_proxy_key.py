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

def create_key(key_name: str, key_dir: str):
    key_file = os.path.join(key_dir, f'{key_name}.pem')
    if not os.path.exists(key_file):
        subprocess.check_output(f"ssh-keygen -m PEM -f {key_file} -N ''", shell=True)
    return key_file

def get_pub_key(key_file: str):
    pub_key_content = subprocess.check_output(f"ssh-keygen -y -f {key_file}", shell=True).decode('utf-8')
    return pub_key_content

def add_key_to_instances(pub_key: str, hosts: list[dict]):
    for host in hosts:
        utils.exec_ssh_command(
            server=host,
            username='ubuntu',
            key_path=SSH_KEY,
            cmd=f'echo "{pub_key}" >> .ssh/authorized_keys'
        )

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

    key_file = create_key(
        key_name=KEY_NAME,
        key_dir=KEY_DIR,
    )

    pub_key = get_pub_key(key_file=key_file)
    
    add_key_to_instances(
        pub_key=pub_key,
        hosts=sql_cluster_hosts,
    )