import boto3
import yaml
import paramiko

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

def exec_ssh_command(server: str, username: str, key_path: str, cmd: str):
    pkey = paramiko.RSAKey.from_private_key_file(key_path)
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=username, pkey=pkey)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
        print("stdout:", ssh_stdout.readlines())
        print("stderr:", ssh_stderr.readlines())
        