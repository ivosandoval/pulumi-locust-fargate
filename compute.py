import os
import json

import pulumi
from pulumi_aws import lambda_, iam

from utils import filebase64sha256, format_resource_name
from storage import bucket

# https://www.pulumi.com/docs/intro/concepts/config/
config = pulumi.Config()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, config.require('dist_directory'))

# Create role for Lambda
lambda_role = iam.Role(
    resource_name=format_resource_name(name='role'),
    description=f'Role used by Lambda to run the `{pulumi.get_project()}-{pulumi.get_stack()}` project',
    assume_role_policy=json.dumps({
      "Version": "2012-10-17",
      "Statement": [{
        "Sid": "",
        "Effect": "Allow",
        "Action": "sts:AssumeRole", 
        "Principal": {
          "Service": [
            "apigateway.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        },
      }]
    }),
)

policy_attachment = iam.RolePolicyAttachment(
    resource_name=format_resource_name(name='policy-attachment'),
    policy_arn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
    role=lambda_role.name,
)

# Create Lambda layer
LAYER_PATH = os.path.join(DIST_DIR, config.require('layer_filename'))
layer = lambda_.LayerVersion(
    resource_name=format_resource_name(name='layer'),
    layer_name=format_resource_name(name='layer'),
    compatible_runtimes=['python3.7'],
    description=f'Layer containing the dependencies for the `{pulumi.get_project()}` ({pulumi.get_stack()}) project',
    code=LAYER_PATH,
    source_code_hash=filebase64sha256(LAYER_PATH),
    # source_code_size=os.path.getsize(LAYER_PATH),
)

# Create Lambda function
PACKAGE_PATH = os.path.join(DIST_DIR, config.require('serverless_service') + '.zip')
function = lambda_.Function(
    resource_name=format_resource_name(name='function'),
    description=f'Lambda function running the f`{pulumi.get_project()}` ({pulumi.get_stack()}) project',
    handler=config.require('serverless_handler'),
    layers=[layer.arn],
    memory_size=128,
    role=lambda_role.arn,
    runtime=config.require('serverless_runtime'),
    tags={
        'PROJECT': pulumi.get_project()
    },
    timeout=30,
    tracing_config=None, # TODO: add AWS X-Ray tracing
    code=PACKAGE_PATH,
    source_code_hash=filebase64sha256(PACKAGE_PATH),
    # source_code_size=os.path.getsize(PACKAGE_PATH),
    environment={
      'variables' : {
        'DEBUG': config.get('DEBUG') or 0,
        'SECRET_KEY': config.require_secret('SECRET_KEY'),
        'AWS_STORAGE_BUCKET_NAME': bucket.bucket,
        'DOMAIN': config.require('subdomain'),
      }
    },
)

# Exports
pulumi.export('function_role_name', lambda_role.name)
pulumi.export('layer_name',  layer.layer_name)
pulumi.export('function_name',  function.name)