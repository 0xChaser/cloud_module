import pulumi

from infra.vpc import create_vpc, create_security_groups
from infra.s3 import (
    create_static_bucket,
    create_data_bucket,
    create_cloudfront_oac,
    create_static_bucket_policy,
)
from infra.secrets import create_db_secret, create_api_key_secret
from infra.iam import (
    create_lambda_role,
    create_rds_monitoring_role,
    create_api_gateway_role,
)
from infra.rds import (
    create_rds_subnet_group,
    create_rds_parameter_group,
    create_rds_instance,
)
from infra.lambda_function import (
    create_lambda_function,
    create_lambda_permission_for_api_gateway,
)
from infra.api_gateway import create_api_gateway
from infra.cloudfront import create_cloudfront_distribution
from infra.waf import create_waf_acl
from infra.cloudwatch import create_dashboard, create_alarms

config = pulumi.Config()
environment = config.get("environment") or "dev"

pulumi.log.info("Creating VPC and networking resources...")

vpc_resources = create_vpc()
vpc = vpc_resources["vpc"]
public_subnets = vpc_resources["public_subnets"]
private_subnets = vpc_resources["private_subnets"]

security_groups = create_security_groups(vpc.id)
lambda_sg = security_groups["lambda_sg"]
rds_sg = security_groups["rds_sg"]

pulumi.log.info("Creating S3 buckets...")

static_bucket = create_static_bucket()
data_bucket = create_data_bucket()

pulumi.log.info("Creating secrets...")

db_secret_resources = create_db_secret()
db_secret = db_secret_resources["secret"]
db_password = db_secret_resources["password"]

api_key_secret_resources = create_api_key_secret()
api_key_secret = api_key_secret_resources["secret"]

pulumi.log.info("Creating IAM roles...")

lambda_role = create_lambda_role(
    data_bucket_arn=data_bucket.arn,
    secrets_arn=db_secret.arn,
)

rds_monitoring_role = create_rds_monitoring_role()
api_gateway_role = create_api_gateway_role()

pulumi.log.info("Creating RDS resources...")

rds_subnet_group = create_rds_subnet_group(
    private_subnet_ids=[subnet.id for subnet in private_subnets]
)

rds_parameter_group = create_rds_parameter_group()

rds_instance = create_rds_instance(
    subnet_group=rds_subnet_group,
    parameter_group=rds_parameter_group,
    security_group_id=rds_sg.id,
    db_password=db_password,
    monitoring_role_arn=rds_monitoring_role.arn,
)

pulumi.log.info("Creating Lambda function...")

lambda_function = create_lambda_function(
    lambda_role=lambda_role,
    lambda_sg_id=lambda_sg.id,
    private_subnet_ids=[subnet.id for subnet in private_subnets],
    db_secret_arn=db_secret.arn,
    data_bucket_name=data_bucket.bucket,
    rds_endpoint=rds_instance.endpoint,
)

pulumi.log.info("Creating API Gateway...")

api_gateway_resources = create_api_gateway(lambda_function)
api = api_gateway_resources["api"]
api_stage = api_gateway_resources["stage"]

# Permission pour API Gateway d'invoquer Lambda
lambda_permission = create_lambda_permission_for_api_gateway(
    lambda_function=lambda_function,
    api_gateway_execution_arn=api.execution_arn,
)

pulumi.log.info("Creating WAF...")

waf_acl = create_waf_acl()

pulumi.log.info("Creating CloudFront distribution...")

cloudfront_oac = create_cloudfront_oac(static_bucket)

cloudfront_distribution = create_cloudfront_distribution(
    static_bucket=static_bucket,
    oac=cloudfront_oac,
    waf_acl_arn=waf_acl.arn,
)

static_bucket_policy = create_static_bucket_policy(
    static_bucket=static_bucket,
    cloudfront_distribution_arn=cloudfront_distribution.arn,
)

pulumi.log.info("Creating CloudWatch resources...")

dashboard = create_dashboard(
    lambda_function_name=lambda_function.name,
    rds_identifier=rds_instance.identifier,
    api_name=api.name,
)

alarms = create_alarms(
    lambda_function_name=lambda_function.name,
    rds_identifier=rds_instance.identifier,
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_ids", [subnet.id for subnet in public_subnets])
pulumi.export("private_subnet_ids", [subnet.id for subnet in private_subnets])

pulumi.export("static_bucket_name", static_bucket.bucket)
pulumi.export("data_bucket_name", data_bucket.bucket)

pulumi.export("rds_endpoint", rds_instance.endpoint)
pulumi.export("rds_port", rds_instance.port)

pulumi.export("lambda_function_name", lambda_function.name)
pulumi.export("lambda_function_arn", lambda_function.arn)

pulumi.export("api_gateway_url", api_stage.invoke_url)
pulumi.export("api_gateway_id", api.id)

pulumi.export("cloudfront_domain", cloudfront_distribution.domain_name)
pulumi.export("cloudfront_distribution_id", cloudfront_distribution.id)

pulumi.export("waf_acl_arn", waf_acl.arn)

pulumi.export("db_secret_arn", db_secret.arn)
pulumi.export("api_key_secret_arn", api_key_secret.arn)

pulumi.export("sns_alerts_topic_arn", alarms["alert_topic"].arn)
