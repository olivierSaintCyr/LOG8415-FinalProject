import utils
from dotenv import load_dotenv
import boto3
import os

def get_sql_cluster_node_role(net_info: dict) -> dict:
    return {
        'master': net_info[0],
        'data_nodes': net_info[1:]
    }

def start_sql_cluster(node_roles: dict):
    def get_start_master_node_cmd():
        return 'sudo /opt/mysqlcluster/home/mysqlc/bin/ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf'
    
    def get_start_data_node_cmd(master_private_hostname: str):
        return f'sudo /opt/mysqlcluster/home/mysqlc/bin/ndbd -c {master_private_hostname}:1186'
    
    # TODO test
    def get_start_sqld_cmd():
        return 'sudo /opt/mysqlcluster/home/mysqlc/bin/mysqld --defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf --user=root'

    # Start master node ndb_mgmd
    utils.exec_ssh_command(
        server=instance_sql_roles['master']['PublicDnsName'],
        username=USERNAME,
        key_path=SSH_KEY_PATH,
        cmd=get_start_master_node_cmd()
    )

    # Connect data nodes to master
    connect_to_master_cmd = get_start_data_node_cmd(instance_sql_roles['master']['PrivateDnsName'])
    for data_node in node_roles['data_nodes']:
        utils.exec_ssh_command(
            server=data_node['PublicDnsName'],
            username=USERNAME,
            key_path=SSH_KEY_PATH,
            cmd=connect_to_master_cmd
        )
    
    # Start sqld server on master
    utils.exec_ssh_command(
        server=instance_sql_roles['master']['PublicDnsName'],
        username=USERNAME,
        key_path=SSH_KEY_PATH,
        cmd=get_start_sqld_cmd()
    )

DEPLOYMENT_FILE = 'fake_deployment_cluster.yml'
CLUSTER_NAME = 'sql_cluster'
USERNAME = 'ubuntu'
SSH_KEY_PATH = 'final_project_gen_key.pem'

if __name__ == '__main__':
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

    instance_network_infos = [
        {
            'InstanceId': description['InstanceId'],  
            'PrivateDnsName': description['PrivateDnsName'],
            'PublicDnsName': description['PublicDnsName'] 
        } for description in instance_descriptions
    ]

    instance_sql_roles = get_sql_cluster_node_role(
        net_info=instance_network_infos
    )

    print(instance_sql_roles)
    
    start_sql_cluster(node_roles=instance_sql_roles)
