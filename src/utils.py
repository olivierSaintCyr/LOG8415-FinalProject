import boto3
import yaml
import paramiko
import os
import subprocess

def get_deployment(deployment_file: str):
    with open(deployment_file, 'r') as f:
        return yaml.full_load(f)

def get_deployment_instances(deployment: dict, cluster_name: str):
    return deployment['clusters'][cluster_name]

def get_cluster_instances(deployment_file: str, cluster_name: str):
    deployment = get_deployment(deployment_file)
    return get_deployment_instances(
        deployment=deployment,
        cluster_name=cluster_name,
    )

def describe_instances(instance_ids: list[str], client):
    return client.describe_instances(
        InstanceIds=instance_ids
    )

def exec_ssh_command(server: str, username: str, key_path: str, cmd: str, wait=True):
    pkey = paramiko.RSAKey.from_private_key_file(key_path)
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=username, pkey=pkey)
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd, timeout=15)
            if wait:
                print("stdout:", ssh_stdout.readlines())
                print("stderr:", ssh_stderr.readlines())
        except TimeoutError:
            print("Command timeout")

def create_key(key_name: str, key_dir: str):
    key_file = os.path.join(key_dir, f'{key_name}.pem')
    if not os.path.exists(key_file):
        subprocess.check_output(f"ssh-keygen -m PEM -f {key_file} -N ''", shell=True)
    return key_file

def get_pub_key(key_file: str):
    pub_key_content = subprocess.check_output(f"ssh-keygen -y -f {key_file}", shell=True).decode('utf-8')
    return pub_key_content

def add_key_to_instances(pub_key: str, hosts: list[dict], key_path: str):
    for host in hosts:
        exec_ssh_command(
            server=host,
            username='ubuntu',
            key_path=key_path,
            cmd=f'''
                grep -qxF "{pub_key}" .ssh/authorized_keys || echo "{pub_key}" >> .ssh/authorized_keys;
            '''
        )

def scp_to_instance(host: str, user: str, key_file: str, files: str, location: str = ''):
    out = subprocess.check_output(f'pwd')
    print(out)
    instance_path = f'/home/{user}' if len(location) == 0 else location
    try:
        out = subprocess.check_output(['scp', '-i', key_file, *files, f'{user}@{host}:{instance_path}'])
    except subprocess.CalledProcessError as e:
        print(e.output)
