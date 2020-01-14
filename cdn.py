from urllib.parse import urlparse

import pulumi
from pulumi_aws import route53, acm, cloudfront

from utils import format_resource_name
from api import deployment
from storage import bucket

config = pulumi.Config()


# Parse the API Gateway URL asynchronously
parsed_url = deployment.invoke_url.apply(urlparse)
# Define API custom origin mapping
# https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html
api_origin = {
    'origin_id'           : f'{pulumi.get_project()}-{pulumi.get_stack()}-website',
    'domain_name'         : parsed_url.netloc,
    'origin_path'         : parsed_url.path,
    'custom_header'       : [
        # These headers are necessary otherwise Django will think that the URL
        # it is serving from is API Gateway's invoke URL
        {
            'name': 'HTTP_X_FORWARDED_HOST',
            'value': config.require('subdomain')
        },
        {
            'name': 'X-Forwarded-Host',
            'value': config.require('subdomain')
        },
    ],
    'custom_origin_config': {
        'http_port'             : 80,
        'https_port'            : 443,
        'origin_protocol_policy': 'https-only',
        'origin_ssl_protocols'  : ['SSLv3', 'TLSv1', 'TLSv1.1', 'TLSv1.2'],
    }
}
static_s3_origin = {
    'origin_id'       : f'{pulumi.get_project()}-{pulumi.get_stack()}-static',
    'domain_name'     : bucket.bucket_domain_name,
}

# Define Cloudfront distribution
# https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html
# https://github.com/pulumi/pulumi-aws/blob/master/sdk/python/pulumi_aws/cloudfront/distribution.py
cdn = cloudfront.Distribution(
    resource_name = format_resource_name(name='cdn'),
    # TODO: Fix "The parameter CNAME contains one or more parameters that are not valid."
    # aliases       = [
    #     'www.example.com', #config.require('subdomain')
    # ],
    comment       = (
        f'CDN for Django-based `{pulumi.get_project()}` project. '
        f'Contains both the APIGW & S3 origins'
    ),
    custom_error_responses=[
        # https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html#custom-error-response-arguments
        {
            'error_caching_min_ttl': 10,
            'error_code'           : error_code,
            'response_code'        : None,
            'response_page_path'   : None,
        }
        for error_code in [400, 403, 404, 500, 504]
    ],
    default_cache_behavior={
        # Default cache is API Gateway
        # https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html#default-cache-behavior-arguments
        'target_origin_id'      : api_origin['origin_id'],
        'allowed_methods'       : ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
        'cached_methods'        : ["GET", "HEAD"],
        'compress'              : True,
        'default_ttl'           : 0,
        'viewer_protocol_policy': 'redirect-to-https',
        'forwarded_values' : {
            'headers': [
                'Accept',
                'Accept-Language',
                'Authorization',
                'Upgrade-Insecure-Requests',
                # Required for Django forms
                'HTTP_X_CSRFTOKEN',
                'x-csrfmiddlewaretoken',
            ],
            'query_string': True,
            'cookies':  {
                'forward': "all"
            },
        },
    },
    # default_root_object=None,
    enabled=True,
    # logging_config=None,
    ordered_cache_behaviors=[
        # First cache is S3 static files
        {
            'allowed_methods': ["GET", "HEAD"],
            'cached_methods' : ["GET", "HEAD"],
            'compress'       : True,
            'default_ttl'    : 120,
            'forwarded_values' : {
                'query_string': False,
                'cookies':  {
                    'forward' :"none"
                },
                'headers': None,
                'query_string_cache_keys': None,
            },
            'path_pattern'          : '/static/*',
            'target_origin_id'      : static_s3_origin['origin_id'],
            'viewer_protocol_policy': 'redirect-to-https',
        }
    ],
    origins=[
        # API Gateway
        api_origin,
        # S3 static
        static_s3_origin,
    ],
    price_class='PriceClass_All',
    restrictions={
        'geo_restriction': {
            'restriction_type': 'none'
        }
    },
    # tags=None,
    viewer_certificate={
        'cloudfront_default_certificate' : True
    },
    wait_for_deployment=False,
    # opts=pulumi.ResourceOptions(
    #     protect=True,
    # )
)
pulumi.export('cdn_domain_name', cdn.domain_name)
