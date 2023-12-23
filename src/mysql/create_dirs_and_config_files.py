import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
import boto3
import utils
from start_sql_cluster import get_sql_cluster_node_role
from generate_cluster_config_files import generate_config_files

CLUSTER_NAME = 'sql_cluster'
DEPLOYMENT_FILE = 'deployment.yml'
SSH_KEY_PATH = 'final_project_gen_key.pem'
DEPLOY_PATH = '/opt/mysqlcluster/deploy'

def get_create_master_dirs_cmds():
    

    dirs = [
        'conf',
        'mysqld_data',
        'ndb_data',
    ]

    return [
        f'sudo mkdir -p {DEPLOY_PATH}',
        f'sudo mkdir {" ".join(os.path.join(DEPLOY_PATH, d_dir) for d_dir in dirs)}'
    ]

def get_create_data_nodes_dirs_cmds():
    return [
        f'sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data',
    ]

def create_dirs_and_config_file(client):
    cluster_config_files = generate_config_files(client=client)

    instance_ids = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name=CLUSTER_NAME,
    )

    instance_infos = utils.describe_instances(
        client=client,
        instance_ids=instance_ids,
    )['Reservations'][0]['Instances']

    cluster_roles = get_sql_cluster_node_role(instance_infos)

    print('Creating directories...')
    utils.exec_ssh_command(
        server=cluster_roles['master']['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd='; '.join(get_create_master_dirs_cmds()),
    )

    for data_node in cluster_roles['data_nodes']:
        utils.exec_ssh_command(
            server=data_node['PublicDnsName'],
            username='ubuntu',
            key_path=SSH_KEY_PATH,
            cmd='; '.join(get_create_data_nodes_dirs_cmds()),
        )
    
    print('Copying config files to master...')
    utils.scp_to_instance(
        host=cluster_roles['master']['PublicDnsName'],
        user='ubuntu',
        key_file=SSH_KEY_PATH,
        files=cluster_config_files,
    )

    utils.exec_ssh_command(
        server=cluster_roles['master']['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd=f'sudo mv {" ".join(os.path.join("/home/ubuntu", os.path.basename(conf)) for conf in cluster_config_files)} {DEPLOY_PATH}/conf',
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

    create_dirs_and_config_file(client=client)
