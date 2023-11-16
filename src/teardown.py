
import traceback
from dotenv import load_dotenv
import boto3 # https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
import os
import yaml

DEPLOY_FILE = 'deployment.yml'

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
elb_client = session.client('elbv2')    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html

# Waits for EC2 instances to reach a desired state.
def ec2_client_wait(instance_ids, event):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/get_waiter.html
    waiter = ec2_client.get_waiter(event)
    return waiter.wait(InstanceIds=instance_ids)

# Deletes an AWS target group.
def deleteTargetGroup(target_group_arn):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2/client/delete_target_group.html
    deleted_target_group = elb_client.delete_target_group(TargetGroupArn=target_group_arn)
    print('DELETED TARGET GROUP ', target_group_arn)
    return deleted_target_group

# Waits for EC2 instances to terminate.
def awaitInstancesTerminated(instance_ids):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/waiter/InstanceTerminated.html
    print('AWAITING INSTANCES TERMINATED ', instance_ids)
    return ec2_client_wait(instance_ids, 'instance_terminated')

# Deregisters EC2 instances from a target group.
def deregisterTargets(instance_ids, target_group_arn, port=80):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2/client/deregister_targets.html
    targets = [{'Id': instance_id, 'Port': port } for instance_id in instance_ids]
    deregistered_targets = elb_client.deregister_targets(
        TargetGroupArn=target_group_arn,
        Targets=targets
    )
    print('DEREGISTERING TARGETS ', instance_ids, ' FROM ', target_group_arn)
    # awaitInstancesDeregistered(instance_ids, target_group_arn)
    return deregistered_targets

# Deletes EC2 instances and their associated key pair.
def deleteInstances(instance_ids, name):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/terminate_instances.html
    key_name = f'{name}_key'
    ec2_client.delete_key_pair(KeyName=key_name)
    print('DELETED KEY ', key_name)
    
    deleted_instances = ec2_client.terminate_instances(InstanceIds=instance_ids)
    awaitInstancesTerminated(instance_ids)
    
    print('DELETED INSTANCES ', instance_ids)
    return deleted_instances

# Deletes an AWS security group by its ID.
def deleteSecurityGroup(security_group_id):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/delete_security_group.html
    deleted_security_group = ec2_client.delete_security_group(GroupId=security_group_id)
    print('DELETED SECURITY GROUP', security_group_id)
    return deleted_security_group

# Teardown configuration for instances, target group, and key pair.
def teardownConfig(instance_ids, name):
    try:
        deleteInstances(instance_ids, name)
    except Exception as e:
        print(e, traceback.format_exc())

# Teardown down AWS resources.
def teardown(clusters, rules, security_group_id):
    try:
        for name, instance_ids in clusters.items():
            teardownConfig(instance_ids, name)
    except Exception as e:
        print(e, traceback.format_exc())
    
    try:
        deleteSecurityGroup(security_group_id)
    except Exception as e:
        print(e, traceback.format_exc())
# Loads YAML deployment file into a dictionary.
def load_deployment(deployment_file: str):
    with open(deployment_file, 'r') as f:
        return yaml.full_load(f)

# Loads YAML deployment file to teardown AWS resources.
if  __name__ == '__main__':
    deployment = load_deployment(DEPLOY_FILE)
    teardown(**deployment)