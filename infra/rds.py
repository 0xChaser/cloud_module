import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"
db_name = config.get("db_name") or "appdb"


def create_rds_subnet_group(private_subnet_ids: list[pulumi.Output]):

    subnet_group = aws.rds.SubnetGroup(
        f"rds-subnet-group-{environment}",
        subnet_ids=private_subnet_ids,
        description="Subnet group for RDS in private subnets",
        tags={
            "Name": f"rds-subnet-group-{environment}",
            "Environment": environment,
        },
    )

    return subnet_group


def create_rds_parameter_group():

    parameter_group = aws.rds.ParameterGroup(
        f"rds-pg-params-{environment}",
        family="postgres17",
        description="Custom parameter group for PostgreSQL 15",
        parameters=[
            aws.rds.ParameterGroupParameterArgs(
                name="log_statement",
                value="all",
            ),
            aws.rds.ParameterGroupParameterArgs(
                name="log_min_duration_statement",
                value="1000",
            ),
        ],
        tags={
            "Name": f"rds-pg-params-{environment}",
            "Environment": environment,
        },
    )

    return parameter_group


def create_rds_instance(
    subnet_group: aws.rds.SubnetGroup,
    parameter_group: aws.rds.ParameterGroup,
    security_group_id: pulumi.Output,
    db_password: str,
    monitoring_role_arn: pulumi.Output,
):

    db_username = config.get("db_username") or "dbadmin"

    rds_instance = aws.rds.Instance(
        f"main-db-{environment}",
        identifier=f"main-db-{environment}",
        engine="postgres",
        engine_version="17.7",
        instance_class="db.t3.micro",
        allocated_storage=20,
        max_allocated_storage=100,
        storage_type="gp3",
        storage_encrypted=True,
        db_name=db_name,
        username=db_username,
        password=db_password,
        db_subnet_group_name=subnet_group.name,
        vpc_security_group_ids=[security_group_id],
        parameter_group_name=parameter_group.name,
        publicly_accessible=False,
        skip_final_snapshot=environment == "dev",
        final_snapshot_identifier=f"main-db-final-{environment}" if environment != "dev" else None,
        backup_retention_period=7,
        backup_window="03:00-04:00",
        maintenance_window="Mon:04:00-Mon:05:00",
        monitoring_interval=60,
        monitoring_role_arn=monitoring_role_arn,
        performance_insights_enabled=True,
        performance_insights_retention_period=7,
        enabled_cloudwatch_logs_exports=["postgresql", "upgrade"],
        deletion_protection=environment == "prod",
        tags={
            "Name": f"main-db-{environment}",
            "Environment": environment,
        },
    )

    return rds_instance
