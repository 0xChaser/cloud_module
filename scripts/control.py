import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_dotenv = _root / ".env"
if _dotenv.exists():
    try:
        import dotenv
        dotenv.load_dotenv(_dotenv)
    except ImportError:
        pass

import boto3
from botocore.exceptions import ClientError


REGION = os.getenv("AWS_REGION") or "eu-west-3"

def lambda_disable(name: str) -> None:
    client = boto3.client("lambda", region_name=REGION)
    client.put_function_concurrency(FunctionName=name, ReservedConcurrentExecutions=0)
    print(f"Lambda '{name}' désactivée (concurrency = 0)")


def lambda_enable(name: str) -> None:
    client = boto3.client("lambda", region_name=REGION)
    client.delete_function_concurrency(FunctionName=name)
    print(f"Lambda '{name}' activée")

def cloudfront_disable(distribution_id: str) -> None:
    client = boto3.client("cloudfront")
    resp = client.get_distribution_config(Id=distribution_id)
    config = resp["DistributionConfig"]
    etag = resp["ETag"]
    if not config["Enabled"]:
        print(f"CloudFront '{distribution_id}' est déjà désactivée")
        return
    config["Enabled"] = False
    client.update_distribution(Id=distribution_id, DistributionConfig=config, IfMatch=etag)
    print(f"CloudFront '{distribution_id}' désactivée")


def cloudfront_enable(distribution_id: str) -> None:
    client = boto3.client("cloudfront")
    resp = client.get_distribution_config(Id=distribution_id)
    config = resp["DistributionConfig"]
    etag = resp["ETag"]
    if config["Enabled"]:
        print(f"CloudFront '{distribution_id}' est déjà activée")
        return
    config["Enabled"] = True
    client.update_distribution(Id=distribution_id, DistributionConfig=config, IfMatch=etag)
    print(f"CloudFront '{distribution_id}' activée")

def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__.strip())
        sys.exit(1)

    resource, action, target = sys.argv[1].lower(), sys.argv[2].lower(), sys.argv[3]

    if resource not in ("lambda", "cloudfront"):
        print("Ressource invalide. Utilisez 'lambda' ou 'cloudfront'.")
        sys.exit(1)
    if action not in ("enable", "disable"):
        print("Action invalide. Utilisez 'enable' ou 'disable'.")
        sys.exit(1)

    try:
        if resource == "lambda":
            (lambda_enable if action == "enable" else lambda_disable)(target)
        else:
            (cloudfront_enable if action == "enable" else cloudfront_disable)(target)
    except ClientError as e:
        print(f"Erreur AWS: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
