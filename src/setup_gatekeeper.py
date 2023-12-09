import boto3
import utils
from dotenv import load_dotenv
import os



DEPLOYMENT_FILE = 'deployment_egress.yml'
DEPLOYMENT_FILE_2 = 'deployment_fake_ingress.yml' # TODO combine both of them
DEPLOYMENT_FILE_3 = 'deployment_proxy.yml' # TODO combine both of them
SSH_KEY_PATH = 'final_project_gen_key.pem'


INGRESS_KEY_NAME = 'ingress_key'
EGRESS_KEY_NAME = 'egress_key'

def get_instances_info(client):
    def order_instance(instance_descriptions, instances_ids: list[str]):
        ordered = [None] * len(instances_ids)
        for description in instance_descriptions:
            instance_id = description['Instances'][0]['InstanceId']
            ordered[instance_ids.index(instance_id)] = description
        return ordered

    instance_ids = utils.get_cluster_instances(
        deployment_file=DEPLOYMENT_FILE,
        cluster_name='gatekeeper-egress',
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

    egress = instance_descriptions[0]['Instances'][0]
    ingress = instance_descriptions[1]['Instances'][0]
    proxy = instance_descriptions[2]['Instances'][0]
    return egress, ingress, proxy

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
        file=key_file,
    )
    print('sending keyfile', key_file, from_public)

    pub_key = utils.get_pub_key(key_file=key_file)
    
    utils.add_key_to_instances(
        pub_key=pub_key,
        hosts=[to_public],
        key_path=SSH_KEY_PATH
    )

def create_ingress_key(ingress_public: str, egress_public: str):
    create_and_add_key(
        from_public=ingress_public,
        to_public=egress_public,
        gen_key_path=INGRESS_KEY_NAME
    )

def create_egress_key(egress_public: str, proxy_public: str):
    create_and_add_key(
        from_public=egress_public,
        to_public=proxy_public,
        gen_key_path=EGRESS_KEY_NAME,
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
    
    egress, ingress, proxy = get_instances_info(client=client)
    
    # Create keys and send it to ingress for ssh tunnel
    create_ingress_key(
        ingress_public=ingress['PublicDnsName'],
        egress_public=egress['PublicDnsName']
    )

    create_egress_key(
        egress_public=egress['PublicDnsName'],
        proxy_public=proxy['PublicDnsName']
    )
    
    # Setup tunnel
    print('INGRESS TUNNEL')
    tunnel_ingress_to_egress_cmd = get_setup_tunnel_cmd(
        port_from=80,
        port_to=80,
        key_path=f'{INGRESS_KEY_NAME}.pem',
        host=egress['PrivateIpAddress'],
        user='ubuntu',
        external=True,
    )
    print(tunnel_ingress_to_egress_cmd)

    utils.exec_ssh_command(
        server=ingress['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd=tunnel_ingress_to_egress_cmd,
    )

    print('EGRESS TUNNEL')
    tunnel_egress_to_proxy_cmd = get_setup_tunnel_cmd(
        port_from=80,
        port_to=3000,
        key_path=f'{EGRESS_KEY_NAME}.pem',
        host=proxy['PrivateIpAddress'],
        user='ubuntu',
    )
    print(tunnel_egress_to_proxy_cmd)

    utils.exec_ssh_command(
        server=egress['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd=tunnel_egress_to_proxy_cmd,
    )

