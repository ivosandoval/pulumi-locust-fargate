import pulumi
from pulumi_aws import iam, apigateway

from utils import filebase64sha256, format_resource_name
from compute import function

config = pulumi.Config()

api = apigateway.RestApi(
    resource_name=format_resource_name(name='api'),
    description=f'API Gateway for `{pulumi.get_project()}` ({pulumi.get_stack()}) project'
)

api_root_method = apigateway.Method(
    resource_name=format_resource_name(name='api-root-method'),
    http_method='ANY', 
    resource_id=api.root_resource_id,
    rest_api=getattr(api, 'id'),
    authorization='NONE',
)

api_root_integration = apigateway.Integration(
    resource_name=format_resource_name(name='api-root-integration'), 
    http_method=api_root_method.http_method,
    integration_http_method='POST',
    resource_id=api.root_resource_id,
    rest_api=getattr(api, 'id'),
    type='AWS_PROXY',
    uri=function.invoke_arn,
    opts=pulumi.ResourceOptions(
        depends_on=[function]
    ),
    
)

api_resource = apigateway.Resource(
    resource_name=format_resource_name(name='api-resource'),
    parent_id=api.root_resource_id,
    path_part='{proxy+}',
    rest_api=getattr(api, 'id'),
)

api_method = apigateway.Method(
    resource_name=format_resource_name(name='api-method'),
    http_method='ANY', 
    resource_id=getattr(api_resource, 'id'),
    rest_api=getattr(api, 'id'),
    authorization='NONE',
)

api_integration = apigateway.Integration(
    resource_name=format_resource_name(name='api-integration'), 
    http_method=api_method.http_method,
    integration_http_method='POST',
    resource_id=getattr(api_resource, 'id'),
    rest_api=getattr(api, 'id'),
    type='AWS_PROXY',
    uri=function.invoke_arn,
    opts=pulumi.ResourceOptions(
        depends_on=[function]
    ),
)

# TODO: deployment should be done as part of the CI pipeline
deployment = apigateway.Deployment(
    resource_name=format_resource_name(name='deployment'),
    description=None,
    rest_api=getattr(api, 'id'),
    # HACK: `stage_description` isn't shown anywhere in the AWS Console
    # We're using it as a caching mechanism in order to re-deploy the API everytime the Pulumi template changes
    stage_description=filebase64sha256(__file__),
    stage_name=pulumi.get_stack(),
    opts=pulumi.ResourceOptions(
        # NB: all methods should be integrated otherwise the Deployment won't work
        depends_on=[
            api_root_method,
            api_root_integration,
            api_method,
            api_integration,
        ]
    )
)

# Exports
pulumi.export('api_name', api.name)
pulumi.export('deployment_invoke_url', deployment.invoke_url)