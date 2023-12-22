from os import path
import sys
sys.path.append(path.join(path.dirname(__file__), '..'))

import boto3
import utils
from dotenv import load_dotenv
import os

DEPLOYMENT_FILE = 'deployment_trusted_host.yml'
DEPLOYMENT_FILE_2 = 'deployment_fake_ingress.yml' # TODO combine both of them
DEPLOYMENT_FILE_3 = 'deployment_proxy.yml' # TODO combine both of them
SSH_KEY_PATH = 'final_project_gen_key.pem'

INGRESS_KEY_NAME = 'ingress_key'
TRUSTED_HOST_KEY_NAME = 'trusted_host_key'

def get_instances_info(client):
    def order_instance(instance_descriptions, instances_ids: list[str]):
        ordered = [None] * len(instances_ids)
        for description in instance_descriptions:
            instance_id = description['Instances'][0]['InstanceId']
            ordered[instance_ids.index(instance_id)] = description
        return ordered

    instance_ids = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name='gatekeeper-trusted-host',
    )

    instance_ids.extend(utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE_2,
        cluster_name='gatekeeper-ingress',
    ))

    instance_ids.extend(utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE_3,
        cluster_name='proxy',
    ))

    instance_descriptions = utils.describe_instances(
        client=client,
        instance_ids=instance_ids,
    )['Reservations']
    instance_descriptions = order_instance(instance_descriptions, instance_ids)

    trusted_host = instance_descriptions[0]['Instances'][0]
    ingress = instance_descriptions[1]['Instances'][0]
    proxy = instance_descriptions[2]['Instances'][0]
    return trusted_host, ingress, proxy

def get_setup_tunnel_cmd(port_from: int, port_to: int, key_path: str, host: str, user: str, external: bool = False):
    from_map = f'0.0.0.0:{port_from}' if external else port_from
    return f'chmod 600 {key_path}; sudo ssh -i "{key_path}" -o StrictHostKeyChecking=no -f -N -L {from_map}:localhost:{port_to} {user}@{host}'

def create_and_add_key(from_public, to_public, gen_key_path):
    key_file = utils.create_key(
        key_name=gen_key_path,
        key_dir='',
    )

    utils.scp_to_instance(
        host=from_public,
        user='ubuntu',
        key_file=SSH_KEY_PATH,
        files=[key_file],
    )
    print('sending keyfile', key_file, from_public)

    pub_key = utils.get_pub_key(key_file=key_file)
    
    utils.add_key_to_instances(
        pub_key=pub_key,
        hosts=[to_public],
        key_path=SSH_KEY_PATH
    )

def create_ingress_key(ingress_public: str, trusted_host_public: str):
    create_and_add_key(
        from_public=ingress_public,
        to_public=trusted_host_public,
        gen_key_path=INGRESS_KEY_NAME
    )

def create_trusted_host_key(trusted_host_public: str, proxy_public: str):
    create_and_add_key(
        from_public=trusted_host_public,
        to_public=proxy_public,
        gen_key_path=TRUSTED_HOST_KEY_NAME,
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
    
    trusted_host, ingress, proxy = get_instances_info(client=client)
    
    # Create keys and send it to ingress for ssh tunnel
    create_ingress_key(
        ingress_public=ingress['PublicDnsName'],
        trusted_host_public=trusted_host['PublicDnsName']
    )

    create_trusted_host_key(
        trusted_host_public=trusted_host['PublicDnsName'],
        proxy_public=proxy['PublicDnsName']
    )
    
    # Setup tunnel
    print('INGRESS TUNNEL')
    tunnel_ingress_to_trusted_host_cmd = get_setup_tunnel_cmd(
        port_from=80,
        port_to=80,
        key_path=f'{INGRESS_KEY_NAME}.pem',
        host=trusted_host['PrivateIpAddress'],
        user='ubuntu',
        external=True,
    )
    print(tunnel_ingress_to_trusted_host_cmd)

    utils.exec_ssh_command(
        server=ingress['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd=tunnel_ingress_to_trusted_host_cmd,
    )

    print('TRUSTED_HOST TUNNEL')
    tunnel_trusted_host_to_proxy_cmd = get_setup_tunnel_cmd(
        port_from=80,
        port_to=3000,
        key_path=f'{TRUSTED_HOST_KEY_NAME}.pem',
        host=proxy['PrivateIpAddress'],
        user='ubuntu',
    )
    print(tunnel_trusted_host_to_proxy_cmd)

    utils.exec_ssh_command(
        server=trusted_host['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd=tunnel_trusted_host_to_proxy_cmd,
    )

