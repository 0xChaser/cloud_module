import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_cloudfront_distribution(
    static_bucket: aws.s3.BucketV2,
    oac: aws.cloudfront.OriginAccessControl,
    waf_acl_arn: pulumi.Output = None,
):

    cache_policy = aws.cloudfront.CachePolicy(
        f"static-cache-policy-{environment}",
        name=f"static-cache-policy-{environment}",
        comment="Cache policy for static content",
        default_ttl=86400,
        max_ttl=31536000,
        min_ttl=1,
        parameters_in_cache_key_and_forwarded_to_origin=aws.cloudfront.CachePolicyParametersInCacheKeyAndForwardedToOriginArgs(
            cookies_config=aws.cloudfront.CachePolicyParametersInCacheKeyAndForwardedToOriginCookiesConfigArgs(
                cookie_behavior="none",
            ),
            headers_config=aws.cloudfront.CachePolicyParametersInCacheKeyAndForwardedToOriginHeadersConfigArgs(
                header_behavior="none",
            ),
            query_strings_config=aws.cloudfront.CachePolicyParametersInCacheKeyAndForwardedToOriginQueryStringsConfigArgs(
                query_string_behavior="none",
            ),
            enable_accept_encoding_brotli=True,
            enable_accept_encoding_gzip=True,
        ),
    )

    origin_request_policy = aws.cloudfront.OriginRequestPolicy(
        f"static-origin-request-policy-{environment}",
        name=f"static-origin-request-policy-{environment}",
        comment="Origin request policy for S3",
        cookies_config=aws.cloudfront.OriginRequestPolicyCookiesConfigArgs(
            cookie_behavior="none",
        ),
        headers_config=aws.cloudfront.OriginRequestPolicyHeadersConfigArgs(
            header_behavior="none",
        ),
        query_strings_config=aws.cloudfront.OriginRequestPolicyQueryStringsConfigArgs(
            query_string_behavior="none",
        ),
    )

    distribution_args = {
        "enabled": True,
        "is_ipv6_enabled": True,
        "comment": f"CloudFront distribution for static content - {environment}",
        "default_root_object": "index.html",
        "price_class": "PriceClass_100",
        "origins": [
            aws.cloudfront.DistributionOriginArgs(
                domain_name=static_bucket.bucket_regional_domain_name,
                origin_id="S3Origin",
                origin_access_control_id=oac.id,
            ),
        ],
        "default_cache_behavior": aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
            allowed_methods=["GET", "HEAD", "OPTIONS"],
            cached_methods=["GET", "HEAD"],
            target_origin_id="S3Origin",
            viewer_protocol_policy="redirect-to-https",
            cache_policy_id=cache_policy.id,
            origin_request_policy_id=origin_request_policy.id,
            compress=True,
        ),
        "restrictions": aws.cloudfront.DistributionRestrictionsArgs(
            geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                restriction_type="none",
            ),
        ),
        "viewer_certificate": aws.cloudfront.DistributionViewerCertificateArgs(
            cloudfront_default_certificate=True,
        ),
        "custom_error_responses": [
            aws.cloudfront.DistributionCustomErrorResponseArgs(
                error_code=404,
                response_code=200,
                response_page_path="/index.html",
                error_caching_min_ttl=10,
            ),
            aws.cloudfront.DistributionCustomErrorResponseArgs(
                error_code=403,
                response_code=200,
                response_page_path="/index.html",
                error_caching_min_ttl=10,
            ),
        ],
        "tags": {
            "Name": f"static-cdn-{environment}",
            "Environment": environment,
        },
    }

    if waf_acl_arn:
        distribution_args["web_acl_id"] = waf_acl_arn

    distribution = aws.cloudfront.Distribution(
        f"static-cdn-{environment}",
        **distribution_args,
    )

    return distribution
