import pulumi
import json
from pulumi_aws import ecs


from utils import format_resource_name

config = pulumi.Config()

ecs_cluster = ecs.Cluster(
    resource_name=format_resource_name(name='eu-west-1'),
    opts=None,
    capacity_providers=["FARGATE_SPOT"]    
)
with open('nginx.json') as f:
    json_data=json.load(f)
    data_str=json.dumps(json_data)

locust_master_task_definiton = ecs.TaskDefinition(
    resource_name=format_resource_name(name='eu-west-1'),
    opts=None,
    container_definitions=data_str,
    family=f'{pulumi.get_stack()}-locust-master',
    cpu="512",
    memory="1GB",
    network_mode="awsvpc",
    execution_role_arn="arn:aws:iam::918040319999:role/ecsTaskExecutionRole",
    requires_compatibilities=[
        "FARGATE"
    ]
) 

locustMasterService = ecs.Service(
    cluster=ecs_cluster.arn,
    resource_name=format_resource_name(name='eu-west-1'),
    task_definition=locust_master_task_definiton.arn,
    network_configuration={
        "security_groups" : ["sg-0eae5b78fc45c4b24"],        
        "subnets" : ["subnet-0409a0a361e0101ad"],
        "assign_public_ip": True
    },
    launch_type="FARGATE",
    desired_count=1
    
)





