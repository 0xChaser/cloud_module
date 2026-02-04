"""
AWS WAF (Web Application Firewall)
"""
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = config.get("environment") or "dev"


def create_waf_acl():
    waf_provider = aws.Provider(
        "waf-provider",
        region="us-east-1",
    )

    waf_acl = aws.wafv2.WebAcl(
        f"cloudfront-waf-{environment}",
        name=f"cloudfront-waf-{environment}",
        description="WAF ACL for CloudFront distribution",
        scope="CLOUDFRONT",
        default_action=aws.wafv2.WebAclDefaultActionArgs(
            allow=aws.wafv2.WebAclDefaultActionAllowArgs(),
        ),
        visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
            cloudwatch_metrics_enabled=True,
            metric_name=f"cloudfront-waf-{environment}",
            sampled_requests_enabled=True,
        ),
        rules=[
            aws.wafv2.WebAclRuleArgs(
                name="AWSManagedRulesCommonRuleSet",
                priority=1,
                override_action=aws.wafv2.WebAclRuleOverrideActionArgs(
                    none=aws.wafv2.WebAclRuleOverrideActionNoneArgs(),
                ),
                statement=aws.wafv2.WebAclRuleStatementArgs(
                    managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                        vendor_name="AWS",
                        name="AWSManagedRulesCommonRuleSet",
                    ),
                ),
                visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                    cloudwatch_metrics_enabled=True,
                    metric_name="AWSManagedRulesCommonRuleSet",
                    sampled_requests_enabled=True,
                ),
            ),
            aws.wafv2.WebAclRuleArgs(
                name="AWSManagedRulesKnownBadInputsRuleSet",
                priority=2,
                override_action=aws.wafv2.WebAclRuleOverrideActionArgs(
                    none=aws.wafv2.WebAclRuleOverrideActionNoneArgs(),
                ),
                statement=aws.wafv2.WebAclRuleStatementArgs(
                    managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                        vendor_name="AWS",
                        name="AWSManagedRulesKnownBadInputsRuleSet",
                    ),
                ),
                visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                    cloudwatch_metrics_enabled=True,
                    metric_name="AWSManagedRulesKnownBadInputsRuleSet",
                    sampled_requests_enabled=True,
                ),
            ),
            aws.wafv2.WebAclRuleArgs(
                name="AWSManagedRulesSQLiRuleSet",
                priority=3,
                override_action=aws.wafv2.WebAclRuleOverrideActionArgs(
                    none=aws.wafv2.WebAclRuleOverrideActionNoneArgs(),
                ),
                statement=aws.wafv2.WebAclRuleStatementArgs(
                    managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                        vendor_name="AWS",
                        name="AWSManagedRulesSQLiRuleSet",
                    ),
                ),
                visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                    cloudwatch_metrics_enabled=True,
                    metric_name="AWSManagedRulesSQLiRuleSet",
                    sampled_requests_enabled=True,
                ),
            ),
            aws.wafv2.WebAclRuleArgs(
                name="RateLimitRule",
                priority=4,
                action=aws.wafv2.WebAclRuleActionArgs(
                    block=aws.wafv2.WebAclRuleActionBlockArgs(),
                ),
                statement=aws.wafv2.WebAclRuleStatementArgs(
                    rate_based_statement=aws.wafv2.WebAclRuleStatementRateBasedStatementArgs(
                        limit=2000,
                        aggregate_key_type="IP",
                    ),
                ),
                visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                    cloudwatch_metrics_enabled=True,
                    metric_name="RateLimitRule",
                    sampled_requests_enabled=True,
                ),
            ),
        ],
        tags={
            "Name": f"cloudfront-waf-{environment}",
            "Environment": environment,
        },
        opts=pulumi.ResourceOptions(provider=waf_provider),
    )

    return waf_acl
