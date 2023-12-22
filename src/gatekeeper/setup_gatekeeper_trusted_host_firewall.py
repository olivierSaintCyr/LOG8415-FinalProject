from dotenv import load_dotenv
import boto3
import os
from os import path
import sys
sys.path.append(path.join(path.dirname(__file__), '..'))
import utils
from gatekeeper.setup_gatekeeper import get_instances_info

def get_firewall_setup_cmds(ingress_ip: str, proxy_ip: str):
    return [
        "sudo ufw allow 22",
        f"sudo ufw allow proto tcp from {ingress_ip} to any port 80",  # Allow HTTP
        "sudo ufw default deny outgoing",  # Deny all outgoing connections
        f"sudo ufw allow out to {proxy_ip} port 80",  # Allow outgoing HTTP to proxy_ip
        "sudo ufw allow out to any port 53",  # Allow outgoing DNS query
        "sudo ufw --force enable",  # Enable the firewall
    ]

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

    trusted, ingress, proxy = get_instances_info(client=client)

    # Add firewall config to trusted-host
    trusted_host_firewall_setup_cmds = get_firewall_setup_cmds(
        ingress_ip=ingress['PrivateIpAddress'],
        proxy_ip=proxy['PrivateIpAddress'],
    )
    trusted_host_firewall_setup_cmd = "; ".join(trusted_host_firewall_setup_cmds)
    print(trusted_host_firewall_setup_cmd)
    utils.exec_ssh_command(
        server=trusted['PublicDnsName'],
        username='ubuntu',
        key_path=SSH_KEY_PATH,
        cmd=trusted_host_firewall_setup_cmd
    )
