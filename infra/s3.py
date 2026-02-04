import json
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_static_bucket():
    
    bucket = aws.s3.BucketV2(
        f"static-content-{environment}",
        tags={
            "Name": f"static-content-{environment}",
            "Environment": environment,
            "Purpose": "Static website content",
        },
    )

    public_access_block = aws.s3.BucketPublicAccessBlock(
        f"static-content-public-access-block-{environment}",
        bucket=bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )

    versioning = aws.s3.BucketVersioningV2(
        f"static-content-versioning-{environment}",
        bucket=bucket.id,
        versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
            status="Enabled",
        ),
    )

    encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
        f"static-content-encryption-{environment}",
        bucket=bucket.id,
        rules=[
            aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
                apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm="AES256",
                ),
            ),
        ],
    )

    return bucket


def create_data_bucket():
    
    bucket = aws.s3.BucketV2(
        f"data-storage-{environment}",
        tags={
            "Name": f"data-storage-{environment}",
            "Environment": environment,
            "Purpose": "Data storage from RDS exports",
        },
    )

    public_access_block = aws.s3.BucketPublicAccessBlock(
        f"data-storage-public-access-block-{environment}",
        bucket=bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )

    versioning = aws.s3.BucketVersioningV2(
        f"data-storage-versioning-{environment}",
        bucket=bucket.id,
        versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
            status="Enabled",
        ),
    )

    encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
        f"data-storage-encryption-{environment}",
        bucket=bucket.id,
        rules=[
            aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
                apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm="AES256",
                ),
            ),
        ],
    )

    lifecycle = aws.s3.BucketLifecycleConfigurationV2(
        f"data-storage-lifecycle-{environment}",
        bucket=bucket.id,
        rules=[
            aws.s3.BucketLifecycleConfigurationV2RuleArgs(
                id="archive-old-data",
                status="Enabled",
                transitions=[
                    aws.s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                        days=90,
                        storage_class="STANDARD_IA",
                    ),
                    aws.s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
                        days=180,
                        storage_class="GLACIER",
                    ),
                ],
            ),
        ],
    )

    return bucket


def create_cloudfront_oac(static_bucket: aws.s3.BucketV2):
    
    oac = aws.cloudfront.OriginAccessControl(
        f"static-oac-{environment}",
        name=f"static-oac-{environment}",
        description="OAC for static content bucket",
        origin_access_control_origin_type="s3",
        signing_behavior="always",
        signing_protocol="sigv4",
    )

    return oac


def create_static_bucket_policy(
    static_bucket: aws.s3.BucketV2,
    cloudfront_distribution_arn: pulumi.Output,
):
    
    account_id = aws.get_caller_identity().account_id

    policy_document = pulumi.Output.all(
        static_bucket.arn, cloudfront_distribution_arn
    ).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowCloudFrontServicePrincipal",
                        "Effect": "Allow",
                        "Principal": {"Service": "cloudfront.amazonaws.com"},
                        "Action": "s3:GetObject",
                        "Resource": f"{args[0]}/*",
                        "Condition": {
                            "StringEquals": {
                                "AWS:SourceArn": args[1],
                            }
                        },
                    }
                ],
            }
        )
    )

    bucket_policy = aws.s3.BucketPolicy(
        f"static-content-policy-{environment}",
        bucket=static_bucket.id,
        policy=policy_document,
    )

    return bucket_policy
