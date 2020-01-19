import pulumi
from pulumi_aws import ecs

from utils import format_resource_name


ecs_cluster = ecs.Cluster(
    resource_name=format_resource_name(name='eu-west-1'),
    opts=None,
    capacity_providers=["FARGATE"]
)



