Cidr_ip='0.0.0.0/0'
Cidr_Ipv6='::0/0'

# Configure the instances for each cluster of the benchmark
cluster_configs = [
    # {
    #     'name': 'standalone',
    #     'zone': 'us-east-1a',
    #     'n_instances': 1,
    #     'instance_type': 't2.micro',
    #     'launch_script': 'src/mysql_standalone.sh',
    #     'security_group': {
    #         'GroupId': 'security_cluster',
    #         'IpPermissions':[
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 22,
    #                 'ToPort': 22,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 3306,
    #                 'ToPort': 3306,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             },
    #         ]
    #     }
    # },
    # {
    #     'name': 'cluster',
    #     'zone': 'us-east-1a',
    #     'n_instances': 4,
    #     'instance_type': 't2.micro',
    #     'launch_script': 'src/mysql_cluster.sh',
    #     'security_group': {
    #         'GroupId': 'security_cluster',
    #         'IpPermissions':[
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 22,
    #                 'ToPort': 22,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 1186,
    #                 'ToPort': 1186,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 3306,
    #                 'ToPort': 3306,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 11860,
    #                 'ToPort': 11860,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             },
    #             {
    #                 'IpProtocol': 'tcp',
    #                 'FromPort': 1024,
    #                 'ToPort': 65535,
    #                 'IpRanges': [{'CidrIp': Cidr_ip}],
    #                 'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
    #             }, # TODO fix
    #         ]
    #     }
    # },
    {
        'name': 'gatekeeper',
        'zone': 'us-east-1a',
        'n_instances': 2,
        'instance_type': 't2.large',
        # 'launch_script': 'src/mysql_cluster.sh'
    },
]