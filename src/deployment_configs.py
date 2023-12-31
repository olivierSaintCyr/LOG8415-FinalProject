Cidr_ip='0.0.0.0/0'
Cidr_Ipv6='::0/0'

# Configure the instances for each cluster of the benchmark
deployment_configs = [
    {
        'name': 'standalone',
        'zone': 'us-east-1a',
        'n_instances': 1,
        'instance_type': 't2.micro',
        'launch_script': 'src/mysql/mysql_standalone.sh',
        'security_group': {
            'GroupName': 'standalone',
            'IpPermissions':[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
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
            ]
        }
    },
    {
        'name': 'sql_bench',
        'zone': 'us-east-1a',
        'n_instances': 1,
        'instance_type': 't2.micro',
        'security_group': {
            'GroupName': 'sql_bench',
            'IpPermissions':[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
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
            ]
        }
    },
    {
        'name': 'sql_cluster',
        'zone': 'us-east-1a',
        'n_instances': 4,
        'instance_type': 't2.micro',
        'launch_script': 'src/mysql/mysql_cluster.sh',
        'security_group': {
            'GroupName': 'security_cluster',
            'IpPermissions':[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
                {
                    'IpProtocol': 'icmp',
                    'FromPort': -1,
                    'ToPort': -1,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 1024,
                    'ToPort': 65535,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
            ]
        }
    },
    {
        'name': 'gatekeeper-ingress',
        'zone': 'us-east-1a',
        'n_instances': 1,
        'instance_type': 't2.large',
        'security_group': {
            'GroupName': 'gatekeeper-ingress',
            'IpPermissions':[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
            ]
        }
    },
    {
        'name': 'gatekeeper-trusted-host',
        'zone': 'us-east-1a',
        'n_instances': 1,
        'instance_type': 't2.large',
        'security_group': {
            'GroupName': 'gatekeeper-trusted-host',
            'IpPermissions':[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
            ]
        }
    },
    {
        'name': 'proxy',
        'zone': 'us-east-1a',
        'n_instances': 1,
        'instance_type': 't2.large',
        'security_group': {
            'GroupName': 'proxy',
            'IpPermissions':[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
                {
                    'IpProtocol': 'icmp',
                    'FromPort': -1,
                    'ToPort': -1,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 3000,
                    'ToPort': 3000,
                    'IpRanges': [{'CidrIp': Cidr_ip}],
                    'Ipv6Ranges': [{ 'CidrIpv6': Cidr_Ipv6 }],
                },
            ]
        }
    }
]