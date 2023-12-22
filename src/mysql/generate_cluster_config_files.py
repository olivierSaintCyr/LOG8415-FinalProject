import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils
from start_sql_cluster import get_sql_cluster_node_role
from dotenv import load_dotenv
import boto3

GENERATED_FILES_LOCATION = 'src/mysql/'
CLUSTER_NAME = 'sql_cluster'
DEPLOYMENT_FILE = 'fake_deployment_cluster.yml'

def generate_my_cnf(path: str, file_name: str = 'my.cnf'):
    content = [
        '[mysqld]',
        'ndbcluster',
        'datadir=/opt/mysqlcluster/deploy/mysqld_data',
        'basedir=/opt/mysqlcluster/home/mysqlc',
        'port=3306',
    ]

    config_file_path = os.path.join(path, file_name)
    with open(config_file_path, 'w') as f:
        f.write('\n'.join(content) + '\n')
    return config_file_path

def generate_config_ini(path: str, client, file_name: str = 'config.ini'):
    def get_master_node_lines(master_info):
        return [
            '[ndb_mgmd]',
            f'hostname={master_info["PrivateDnsName"]}',
            'datadir=/opt/mysqlcluster/deploy/ndb_data',
            'nodeid=1',
            '',
            '[ndbd default]',
            'noofreplicas=3',
            'datadir=/opt/mysqlcluster/deploy/ndb_data',
        ]
    
    def get_data_node_lines(data_node_info, node_id: int):
        return [
            '[ndbd]',
            f'hostname={data_node_info["PrivateDnsName"]}',
            f'nodeid={node_id}',
        ]
    
    def get_sqld_lines():
        return [
            '[mysqld]',
            'nodeid=50',
        ]

    
    instance_ids = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name=CLUSTER_NAME,
    )

    instance_infos = utils.describe_instances(
        client=client,
        instance_ids=instance_ids,
    )['Reservations'][0]['Instances']

    cluster_roles = get_sql_cluster_node_role(instance_infos)
    
    config_file_path = os.path.join(path, file_name)
    with open(config_file_path, 'w') as f:
        master_node_lines = get_master_node_lines(cluster_roles['master'])
        f.write('\n'.join(master_node_lines) + '\n\n')
        for node_id, data_node in enumerate(cluster_roles['data_nodes'], start=2):
            data_node_lines = get_data_node_lines(data_node, node_id)
            f.write('\n'.join(data_node_lines) + '\n\n')

        sqld_lines = get_sqld_lines()
        f.write('\n'.join(sqld_lines) + '\n')
    
    return config_file_path

def generate_config_files(client):
    print('Generating config file for mysql cluster...')
    return [
        generate_my_cnf(
            path=GENERATED_FILES_LOCATION
        ),
        generate_config_ini(
            path=GENERATED_FILES_LOCATION,
            client=client
        )
    ]

if __name__ == '__main__':
    load_dotenv()
    session = boto3.session.Session(
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key'),
        aws_session_token=os.getenv('aws_session_token'),
        region_name='us-east-1',
    )
    client = session.client('ec2')
    
    print(generate_config_files(client=client))
