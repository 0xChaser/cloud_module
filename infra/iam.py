import json
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_lambda_role(
    data_bucket_arn: pulumi.Output,
    secrets_arn: pulumi.Output,
):

    assume_role_policy = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                }
            ],
        }
    )

    lambda_role = aws.iam.Role(
        f"lambda-role-{environment}",
        assume_role_policy=assume_role_policy,
        tags={
            "Name": f"lambda-role-{environment}",
            "Environment": environment,
        },
    )

    basic_policy = aws.iam.RolePolicyAttachment(
        f"lambda-basic-policy-{environment}",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    )

    custom_policy_document = pulumi.Output.all(data_bucket_arn, secrets_arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "S3Access",
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:ListBucket",
                        ],
                        "Resource": [args[0], f"{args[0]}/*"],
                    },
                    {
                        "Sid": "SecretsManagerAccess",
                        "Effect": "Allow",
                        "Action": [
                            "secretsmanager:GetSecretValue",
                            "secretsmanager:DescribeSecret",
                        ],
                        "Resource": args[1],
                    },
                    {
                        "Sid": "CloudWatchLogs",
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                        ],
                        "Resource": "arn:aws:logs:*:*:*",
                    },
                ],
            }
        )
    )

    custom_policy = aws.iam.RolePolicy(
        f"lambda-custom-policy-{environment}",
        role=lambda_role.id,
        policy=custom_policy_document,
    )

    return lambda_role


def create_rds_monitoring_role():

    assume_role_policy = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "monitoring.rds.amazonaws.com"},
                }
            ],
        }
    )

    rds_monitoring_role = aws.iam.Role(
        f"rds-monitoring-role-{environment}",
        assume_role_policy=assume_role_policy,
        tags={
            "Name": f"rds-monitoring-role-{environment}",
            "Environment": environment,
        },
    )

    aws.iam.RolePolicyAttachment(
        f"rds-monitoring-policy-{environment}",
        role=rds_monitoring_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole",
    )

    return rds_monitoring_role


def create_api_gateway_role():

    assume_role_policy = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "apigateway.amazonaws.com"},
                }
            ],
        }
    )

    api_gw_role = aws.iam.Role(
        f"api-gateway-role-{environment}",
        assume_role_policy=assume_role_policy,
        tags={
            "Name": f"api-gateway-role-{environment}",
            "Environment": environment,
        },
    )

    aws.iam.RolePolicyAttachment(
        f"api-gateway-cloudwatch-policy-{environment}",
        role=api_gw_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs",
    )

    return api_gw_role
