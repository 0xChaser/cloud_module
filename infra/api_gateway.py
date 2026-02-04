import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_api_gateway(lambda_function: aws.lambda_.Function):

    api = aws.apigatewayv2.Api(
        f"main-api-{environment}",
        name=f"main-api-{environment}",
        protocol_type="HTTP",
        description="Main API Gateway for the application",
        cors_configuration=aws.apigatewayv2.ApiCorsConfigurationArgs(
            allow_origins=["*"],
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-Api-Key"],
            max_age=300,
        ),
        tags={
            "Name": f"main-api-{environment}",
            "Environment": environment,
        },
    )

    integration = aws.apigatewayv2.Integration(
        f"lambda-integration-{environment}",
        api_id=api.id,
        integration_type="AWS_PROXY",
        integration_uri=lambda_function.arn,
        integration_method="POST",
        payload_format_version="2.0",
    )

    route = aws.apigatewayv2.Route(
        f"default-route-{environment}",
        api_id=api.id,
        route_key="$default",
        target=integration.id.apply(lambda id: f"integrations/{id}"),
    )

    api_route = aws.apigatewayv2.Route(
        f"api-route-{environment}",
        api_id=api.id,
        route_key="ANY /api/{proxy+}",
        target=integration.id.apply(lambda id: f"integrations/{id}"),
    )

    stage = aws.apigatewayv2.Stage(
        f"api-stage-{environment}",
        api_id=api.id,
        name=environment,
        auto_deploy=True,
        access_log_settings=aws.apigatewayv2.StageAccessLogSettingsArgs(
            destination_arn=create_api_log_group().arn,
            format='{"requestId":"$context.requestId","ip":"$context.identity.sourceIp","requestTime":"$context.requestTime","httpMethod":"$context.httpMethod","routeKey":"$context.routeKey","status":"$context.status","responseLength":"$context.responseLength"}',
        ),
        tags={
            "Name": f"api-stage-{environment}",
            "Environment": environment,
        },
    )

    return {
        "api": api,
        "stage": stage,
        "integration": integration,
    }


def create_api_log_group():

    log_group = aws.cloudwatch.LogGroup(
        f"api-gateway-logs-{environment}",
        name=f"/aws/api-gateway/main-api-{environment}",
        retention_in_days=14,
        tags={
            "Name": f"api-gateway-logs-{environment}",
            "Environment": environment,
        },
    )

    return log_group
