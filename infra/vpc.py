import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_vpc():
    
    vpc = aws.ec2.Vpc(
        f"main-vpc-{environment}",
        cidr_block="10.0.0.0/16",
        enable_dns_hostnames=True,
        enable_dns_support=True,
        tags={
            "Name": f"main-vpc-{environment}",
            "Environment": environment,
        },
    )

    igw = aws.ec2.InternetGateway(
        f"main-igw-{environment}",
        vpc_id=vpc.id,
        tags={
            "Name": f"main-igw-{environment}",
            "Environment": environment,
        },
    )

    azs = aws.get_availability_zones(state="available")

    public_subnets = []
    for i, az in enumerate(azs.names[:2]):
        subnet = aws.ec2.Subnet(
            f"public-subnet-{i}-{environment}",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i}.0/24",
            availability_zone=az,
            map_public_ip_on_launch=True,
            tags={
                "Name": f"public-subnet-{i}-{environment}",
                "Environment": environment,
                "Type": "public",
            },
        )
        public_subnets.append(subnet)

    private_subnets = []
    for i, az in enumerate(azs.names[:2]):
        subnet = aws.ec2.Subnet(
            f"private-subnet-{i}-{environment}",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i + 10}.0/24",
            availability_zone=az,
            map_public_ip_on_launch=False,
            tags={
                "Name": f"private-subnet-{i}-{environment}",
                "Environment": environment,
                "Type": "private",
            },
        )
        private_subnets.append(subnet)

    public_rt = aws.ec2.RouteTable(
        f"public-rt-{environment}",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=igw.id,
            ),
        ],
        tags={
            "Name": f"public-rt-{environment}",
            "Environment": environment,
        },
    )

    for i, subnet in enumerate(public_subnets):
        aws.ec2.RouteTableAssociation(
            f"public-rt-assoc-{i}-{environment}",
            subnet_id=subnet.id,
            route_table_id=public_rt.id,
        )

    nat_eip = aws.ec2.Eip(
        f"nat-eip-{environment}",
        domain="vpc",
        tags={
            "Name": f"nat-eip-{environment}",
            "Environment": environment,
        },
    )

    nat_gw = aws.ec2.NatGateway(
        f"nat-gw-{environment}",
        allocation_id=nat_eip.id,
        subnet_id=public_subnets[0].id,
        tags={
            "Name": f"nat-gw-{environment}",
            "Environment": environment,
        },
    )

    private_rt = aws.ec2.RouteTable(
        f"private-rt-{environment}",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                nat_gateway_id=nat_gw.id,
            ),
        ],
        tags={
            "Name": f"private-rt-{environment}",
            "Environment": environment,
        },
    )

    for i, subnet in enumerate(private_subnets):
        aws.ec2.RouteTableAssociation(
            f"private-rt-assoc-{i}-{environment}",
            subnet_id=subnet.id,
            route_table_id=private_rt.id,
        )

    return {
        "vpc": vpc,
        "public_subnets": public_subnets,
        "private_subnets": private_subnets,
        "igw": igw,
        "nat_gw": nat_gw,
    }


def create_security_groups(vpc_id: pulumi.Output):

    lambda_sg = aws.ec2.SecurityGroup(
        f"lambda-sg-{environment}",
        vpc_id=vpc_id,
        description="Security group for Lambda functions",
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=["0.0.0.0/0"],
                description="Allow all outbound traffic",
            ),
        ],
        tags={
            "Name": f"lambda-sg-{environment}",
            "Environment": environment,
        },
    )

    rds_sg = aws.ec2.SecurityGroup(
        f"rds-sg-{environment}",
        vpc_id=vpc_id,
        description="Security group for RDS database",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                from_port=5432,
                to_port=5432,
                protocol="tcp",
                security_groups=[lambda_sg.id],
                description="Allow PostgreSQL from Lambda",
            ),
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=["0.0.0.0/0"],
                description="Allow all outbound traffic",
            ),
        ],
        tags={
            "Name": f"rds-sg-{environment}",
            "Environment": environment,
        },
    )

    return {
        "lambda_sg": lambda_sg,
        "rds_sg": rds_sg,
    }
