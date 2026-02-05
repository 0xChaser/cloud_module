import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_dashboard(
    lambda_function_name: pulumi.Output,
    rds_identifier: pulumi.Output,
    api_name: pulumi.Output,
):

    dashboard_body = pulumi.Output.all(
        lambda_function_name, rds_identifier, api_name
    ).apply(
        lambda args: f'''{{
    "widgets": [
        {{
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {{
                "title": "Lambda Invocations",
                "metrics": [
                    ["AWS/Lambda", "Invocations", "FunctionName", "{args[0]}"],
                    [".", "Errors", ".", "."],
                    [".", "Duration", ".", ".", {{ "stat": "Average" }}]
                ],
                "region": "eu-west-3",
                "period": 300
            }}
        }},
        {{
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {{
                "title": "RDS Performance",
                "metrics": [
                    ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "{args[1]}"],
                    [".", "DatabaseConnections", ".", "."],
                    [".", "FreeStorageSpace", ".", "."]
                ],
                "region": "eu-west-3",
                "period": 300
            }}
        }},
        {{
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {{
                "title": "API Gateway",
                "metrics": [
                    ["AWS/ApiGateway", "Count", "ApiName", "{args[2]}"],
                    [".", "4XXError", ".", "."],
                    [".", "5XXError", ".", "."],
                    [".", "Latency", ".", ".", {{ "stat": "Average" }}]
                ],
                "region": "eu-west-3",
                "period": 300
            }}
        }},
        {{
            "type": "metric",
            "x": 12,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {{
                "title": "Lambda Concurrent Executions",
                "metrics": [
                    ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "{args[0]}"],
                    [".", "Throttles", ".", "."]
                ],
                "region": "eu-west-3",
                "period": 300
            }}
        }}
    ]
}}'''
    )

    dashboard = aws.cloudwatch.Dashboard(
        f"main-dashboard-{environment}",
        dashboard_name=f"main-dashboard-{environment}",
        dashboard_body=dashboard_body,
    )

    return dashboard


def create_alarms(
    lambda_function_name: pulumi.Output,
    rds_identifier: pulumi.Output,
):

    alert_topic = aws.sns.Topic(
        f"alerts-topic-{environment}",
        name=f"alerts-topic-{environment}",
        tags={
            "Name": f"alerts-topic-{environment}",
            "Environment": environment,
        },
    )

    lambda_error_alarm = aws.cloudwatch.MetricAlarm(
        f"lambda-errors-alarm-{environment}",
        name=f"lambda-errors-{environment}",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=2,
        metric_name="Errors",
        namespace="AWS/Lambda",
        period=300,
        statistic="Sum",
        threshold=5,
        alarm_description="Lambda function errors exceeded threshold",
        dimensions={
            "FunctionName": lambda_function_name,
        },
        alarm_actions=[alert_topic.arn],
        ok_actions=[alert_topic.arn],
        tags={
            "Name": f"lambda-errors-alarm-{environment}",
            "Environment": environment,
        },
    )

    lambda_duration_alarm = aws.cloudwatch.MetricAlarm(
        f"lambda-duration-alarm-{environment}",
        name=f"lambda-duration-{environment}",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=3,
        metric_name="Duration",
        namespace="AWS/Lambda",
        period=300,
        statistic="Average",
        threshold=25000,
        alarm_description="Lambda function duration approaching timeout",
        dimensions={
            "FunctionName": lambda_function_name,
        },
        alarm_actions=[alert_topic.arn],
        tags={
            "Name": f"lambda-duration-alarm-{environment}",
            "Environment": environment,
        },
    )

    rds_cpu_alarm = aws.cloudwatch.MetricAlarm(
        f"rds-cpu-alarm-{environment}",
        name=f"rds-cpu-{environment}",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=3,
        metric_name="CPUUtilization",
        namespace="AWS/RDS",
        period=300,
        statistic="Average",
        threshold=80,
        alarm_description="RDS CPU utilization exceeded 80%",
        dimensions={
            "DBInstanceIdentifier": rds_identifier,
        },
        alarm_actions=[alert_topic.arn],
        ok_actions=[alert_topic.arn],
        tags={
            "Name": f"rds-cpu-alarm-{environment}",
            "Environment": environment,
        },
    )

    rds_storage_alarm = aws.cloudwatch.MetricAlarm(
        f"rds-storage-alarm-{environment}",
        name=f"rds-storage-{environment}",
        comparison_operator="LessThanThreshold",
        evaluation_periods=2,
        metric_name="FreeStorageSpace",
        namespace="AWS/RDS",
        period=300,
        statistic="Average",
        threshold=5368709120,
        alarm_description="RDS free storage space below 5GB",
        dimensions={
            "DBInstanceIdentifier": rds_identifier,
        },
        alarm_actions=[alert_topic.arn],
        ok_actions=[alert_topic.arn],
        tags={
            "Name": f"rds-storage-alarm-{environment}",
            "Environment": environment,
        },
    )

    rds_connections_alarm = aws.cloudwatch.MetricAlarm(
        f"rds-connections-alarm-{environment}",
        name=f"rds-connections-{environment}",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=2,
        metric_name="DatabaseConnections",
        namespace="AWS/RDS",
        period=300,
        statistic="Average",
        threshold=80,
        alarm_description="RDS database connections exceeded threshold",
        dimensions={
            "DBInstanceIdentifier": rds_identifier,
        },
        alarm_actions=[alert_topic.arn],
        tags={
            "Name": f"rds-connections-alarm-{environment}",
            "Environment": environment,
        },
    )

    return {
        "alert_topic": alert_topic,
        "lambda_error_alarm": lambda_error_alarm,
        "lambda_duration_alarm": lambda_duration_alarm,
        "rds_cpu_alarm": rds_cpu_alarm,
        "rds_storage_alarm": rds_storage_alarm,
        "rds_connections_alarm": rds_connections_alarm,
    }
