import json
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_lambda_function(
    lambda_role: aws.iam.Role,
    lambda_sg_id: pulumi.Output,
    private_subnet_ids: list[pulumi.Output],
    db_secret_arn: pulumi.Output,
    data_bucket_name: pulumi.Output,
    rds_endpoint: pulumi.Output,
):

    lambda_code = """
import json

def handler(event, context):
    try:        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Lamdba is up brother',
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
"""

    lambda_archive = pulumi.AssetArchive(
        {
            "lambda_function.py": pulumi.StringAsset(lambda_code),
        }
    )

    log_group = aws.cloudwatch.LogGroup(
        f"lambda-logs-{environment}",
        name=f"/aws/lambda/api-handler-{environment}",
        retention_in_days=14,
        tags={
            "Name": f"lambda-logs-{environment}",
            "Environment": environment,
        },
    )

    lambda_function = aws.lambda_.Function(
        f"api-handler-{environment}",
        name=f"api-handler-{environment}",
        runtime="python3.11",
        handler="lambda_function.handler",
        role=lambda_role.arn,
        code=lambda_archive,
        timeout=30,
        memory_size=256,
        vpc_config=aws.lambda_.FunctionVpcConfigArgs(
            security_group_ids=[lambda_sg_id],
            subnet_ids=private_subnet_ids,
        ),
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables=pulumi.Output.all(
                db_secret_arn, data_bucket_name, rds_endpoint
            ).apply(
                lambda args: {
                    "ENVIRONMENT": environment,
                    "DB_SECRET_ARN": args[0],
                    "DATA_BUCKET": args[1],
                    "DB_HOST": args[2],
                    "DB_NAME": config.get("db_name") or "appdb",
                }
            ),
        ),
        tags={
            "Name": f"api-handler-{environment}",
            "Environment": environment,
        },
        opts=pulumi.ResourceOptions(depends_on=[log_group]),
    )

    return lambda_function


def create_lambda_permission_for_api_gateway(
    lambda_function: aws.lambda_.Function,
    api_gateway_execution_arn: pulumi.Output,
):

    permission = aws.lambda_.Permission(
        f"api-gateway-lambda-permission-{environment}",
        action="lambda:InvokeFunction",
        function=lambda_function.name,
        principal="apigateway.amazonaws.com",
        source_arn=api_gateway_execution_arn.apply(lambda arn: f"{arn}/*/*"),
    )

    return permission
