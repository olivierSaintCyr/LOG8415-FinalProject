from dotenv import load_dotenv
import boto3
import os
import utils
from gatekeeper.setup_gatekeeper import get_instances_info

def get_firewall_setup_cmds(ingress_ip: str, proxy_ip: str):
    return [
        "sudo iptables -F",
        "sudo iptables -P INPUT DROP",
        "sudo iptables -P FORWARD DROP",
        "sudo iptables -P OUTPUT DROP",
        
        "sudo iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT",
        "sudo iptables -A OUTPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT",

        "sudo iptables -A OUTPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT",
        "sudo iptables -A INPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT",

        f"sudo iptables -A INPUT -p tcp -s {ingress_ip} --dport 80 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT",
        f"sudo iptables -A OUTPUT -p tcp -s {ingress_ip} --sport 80 -m conntrack --ctstate ESTABLISHED -j ACCEPT",

        f"sudo iptables -A OUTPUT -p tcp -d {proxy_ip} --dport 80 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT"
        f"sudo iptables -A INPUT -p tcp -s {proxy_ip} --sport 80 -m conntrack --ctstate ESTABLISHED -j ACCEPT"
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
