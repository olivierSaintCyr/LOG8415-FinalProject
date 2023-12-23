from os import path
import sys
sys.path.append(path.join(path.dirname(__file__), '..'))

import utils
from dotenv import load_dotenv
import os
import boto3
import json
import proxy.generate_proxy_config as generate_proxy_config

DEPLOYMENT_FILE = 'deployment_proxy.yml'
SSH_KEY_FILE = 'final_project_gen_key.pem'
FILES_TO_SCP = [
    'src/proxy/requirements.txt',
    generate_proxy_config.PROXY_CONFIG_PATH,
    'src/proxy/proxy_key.pem',
    'src/proxy/app.py'
]

def get_deployment_cmds(proxy_hostname):
    return [
        'sudo NEEDRESTART_MODE=a apt-get update -y',
        'sudo NEEDRESTART_MODE=a apt-get install python3-pip -y',
        'sudo NEEDRESTART_MODE=a pip3 install -r requirements.txt',
        'sudo pkill -f "python3 app.py"',
        'nohup sudo python3 app.py &',
    ]

def deploy_proxy(client):
    generate_proxy_config.generate_proxy_config(client=client)
    
    instance_id = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name='proxy'
    )[0]

    instance_description = utils.describe_instances(
        client=client,
        instance_ids=[instance_id],
    )['Reservations'][0]['Instances'][0]

    proxy_hostname = instance_description['PublicDnsName']\
    
    files = ' '.join(FILES_TO_SCP)

    utils.scp_to_instance(
        host=proxy_hostname,
        user='ubuntu',
        key_file=SSH_KEY_FILE,
        files=FILES_TO_SCP
    )

    deployment_cmds = get_deployment_cmds(proxy_hostname)
    for cmd in deployment_cmds:
        utils.exec_ssh_command(
            server=proxy_hostname,
            username='ubuntu',
            key_path=SSH_KEY_FILE,
            cmd=cmd
        )

if __name__ == '__main__':
    load_dotenv()
    session = boto3.session.Session(
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key'),
        aws_session_token=os.getenv('aws_session_token'),
        region_name='us-east-1',
    )
    client = session.client('ec2')

    deploy_proxy(client=client)

