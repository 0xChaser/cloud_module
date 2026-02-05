"""
AWS Secrets Manager
"""
import json
import pulumi
import pulumi_aws as aws
import secrets
import string

config = pulumi.Config()
environment = config.get("environment") or "dev"
db_username = config.get("db_username") or "dbadmin"


def generate_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_db_secret():

    db_password = generate_password()

    secret = aws.secretsmanager.Secret(
        f"db-credentials-{environment}",
        name=f"db-credentials-{environment}",
        description="Database credentials for RDS",
        tags={
            "Name": f"db-credentials-{environment}",
            "Environment": environment,
        },
    )

    secret_value = aws.secretsmanager.SecretVersion(
        f"db-credentials-version-{environment}",
        secret_id=secret.id,
        secret_string=json.dumps(
            {
                "username": db_username,
                "password": db_password,
            }
        ),
    )

    return {
        "secret": secret,
        "secret_version": secret_value,
        "password": db_password,
    }


def create_api_key_secret():

    api_key = generate_password(48)

    secret = aws.secretsmanager.Secret(
        f"api-keys-{environment}",
        name=f"api-keys-{environment}",
        description="API keys for external services",
        tags={
            "Name": f"api-keys-{environment}",
            "Environment": environment,
        },
    )

    secret_value = aws.secretsmanager.SecretVersion(
        f"api-keys-version-{environment}",
        secret_id=secret.id,
        secret_string=json.dumps(
            {
                "internal_api_key": api_key,
            }
        ),
    )

    return {
        "secret": secret,
        "secret_version": secret_value,
    }
