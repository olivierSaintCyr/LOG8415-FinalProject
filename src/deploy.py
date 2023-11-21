import boto3 # https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
import botocore
import os
import yaml
from dotenv import load_dotenv
import traceback
import sys
from teardown import teardown
from cluster_configs import cluster_configs

LAUNCH_APP_SCRIPT = 'src/mysql_standalone.sh'
DEPLOY_FILE = 'deployment.yml'

key_name = 'final_project_gen_key'

# Retrieve the keys and tokens to access AWS
load_dotenv()
session = boto3.session.Session(
    aws_access_key_id=os.getenv('aws_access_key_id'),
    aws_secret_access_key=os.getenv('aws_secret_access_key'),
    aws_session_token=os.getenv('aws_session_token'),
    region_name='us-east-1',
)

# Get clients and ressources
ec2_ressource = session.resource('ec2') # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html
ec2_client = session.client('ec2')      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html


# This function reads a file and returns its content.
def get_launch_app_script_content(path: str):
    with open(path, 'r') as file:
        return file.read()
    
# Returns a list of subnet IDs.
def get_subnet_ids():
    return [subnet['SubnetId'] for subnet in ec2_client.describe_subnets()['Subnets']]

# Retrieves the ID of the default VPC.
def get_vpc_id():
    vpcs = ec2_client.describe_vpcs()['Vpcs']
    assert len(vpcs) == 1
    return vpcs[0]['VpcId']

# Function sets up cluster config, creates target group, instances, and registers targets.
def setup_config(security_group_id, zone, name, n_instances, instance_type, launch_script):
    print('APPLYTING CONFIG ', name)
    instance_ids = []
    try:
        instance_ids = create_instances(n_instances, security_group_id, zone, name, launch_script, instance_type)
    except Exception as e:
        print(e, traceback.format_exc())
        sys.exit(1)
    return instance_ids

def is_key_pair_exists(key_name):
    try:
        ec2_client.describe_key_pairs(KeyNames=[
            key_name,
        ])
        return True
    except:
        return False
# Creates EC2 instances with specified parameters and waits for them to be running.
def create_instances(n_instances, security_group_id, zone, cluster_name, launch_script=LAUNCH_APP_SCRIPT, instance_type='t2.micro', image_id='ami-053b0d53c279acc90'):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/service-resource/create_instances.html
    
    
    if not is_key_pair_exists(key_name):
        key_pair = ec2_client.create_key_pair(
            KeyName=key_name,
            KeyFormat='pem'
        )
        print('CREATED KEY ', key_name)

        with open(f'{cluster_name}_key.pem', 'w') as f:
            f.write(key_pair['KeyMaterial'])
    
    created_instances = ec2_client.run_instances(
        ImageId=image_id,
        InstanceType=instance_type,
        MinCount=n_instances,
        MaxCount=n_instances,
        Placement={
            'AvailabilityZone': zone,
        },
        SecurityGroupIds=[security_group_id],
        Monitoring={ 'Enabled': True },
        UserData=get_launch_app_script_content(launch_script),
        KeyName=key_name
    )
    instance_ids = [created_instance['InstanceId'] for created_instance in created_instances['Instances']]
    print('CREATED INSTANCES ', instance_ids)
    await_instances_running(instance_ids)
    return instance_ids

# Waits for EC2 instances to be running.
def await_instances_running(instance_ids):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/waiter/InstanceRunning.html
    print('AWAITING INSTANCES RUNNING ', instance_ids)
    return ec2_client_wait(instance_ids, 'instance_running')

# Waits for a specified event on EC2 instances.
def ec2_client_wait(instance_ids, event):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/get_waiter.html
    waiter = ec2_client.get_waiter(event)
    return waiter.wait(InstanceIds=instance_ids)

# Creates a security group and authorizes ingress for specified ports.
def create_security_group(name='mySecurityGroup', description='mySecurityGroupDescription'):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/create_security_group.html
    created_security_group = ec2_client.create_security_group(GroupName=name, Description=description)#, VpcId=vpc_id)

    security_group_id = created_security_group['GroupId']
    print('CREATED SECURITY GROUP', security_group_id)
    authorize_security_group(security_group_id)
    return security_group_id

# This function authorizes security group ingress for specified ports.
def authorize_security_group(security_group_id, Cidr_ip='0.0.0.0/0', Cidr_Ipv6='::0/0'):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/authorize_security_group_ingress.html
    authorized_security_group = ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': Cidr_ip}],
                'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 1186,
                'ToPort': 1186,
                'IpRanges': [{'CidrIp': Cidr_ip}],
                'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'IpRanges': [{'CidrIp': Cidr_ip}],
                'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 11860,
                'ToPort': 11860,
                'IpRanges': [{'CidrIp': Cidr_ip}],
                'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 1024,
                'ToPort': 65535,
                'IpRanges': [{'CidrIp': Cidr_ip}],
                'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
            }, # TODO fix
        ],
    )
    print('AUTHORIZED SECURITY GROUP', security_group_id)
    return authorized_security_group

def save_deployment(deploy_info: str, deployment_file: str):
    with open(deployment_file, 'w') as f:
        yaml.dump(deploy_info, f)

###############
# The main function that executes the deployment process, which create and configure an Elastic Load Balancer, EC2 instances and security groups.
def run():
    clusters = {} # instance ids, target_group_arn
    rules = {} # rules
    try:
        for cluster_config in cluster_configs:
            security_group_id = create_security_group(name=f'security_{cluster_config["name"]}')
            instance_ids = setup_config(security_group_id, **cluster_config)
            clusters[cluster_config['name']] = instance_ids

        rule_priority = 0
        for cluster_config in cluster_configs:
            instance_ids = clusters[cluster_config['name']]
            rule_priority += 1

        print(' -> COMPLETED WITHOUT ERRORS')

    except botocore.exceptions.ClientError as error:
        error_code = error.response['Error']['Code']
        if error_code in ['AuthFailure', 'UnauthorizedOperation']:
            print(" -> AWS CLIENT ERROR : UPDATE ENVIRONMENT KEYS", error)
            sys.exit(1)
        
        print(error, traceback.format_exc())
        teardown(clusters, rules, security_group_id)
        sys.exit(1)
    
    except Exception as error:
        print(error, traceback.format_exc())
        teardown(clusters, rules, security_group_id)
        sys.exit(1)

    deployment = {
        'clusters': clusters,
        'rules': rules,
        'security_group_id': security_group_id,

    }
    save_deployment(deployment, DEPLOY_FILE)
    
if __name__=='__main__':
    run()
