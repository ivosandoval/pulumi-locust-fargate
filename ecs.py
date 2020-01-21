import pulumi
from pulumi_aws import ecs
from utils import json_as_string_from_file



from utils import format_resource_name

config = pulumi.Config()

ecs_cluster = ecs.Cluster(
    resource_name=format_resource_name(name='eu-west-1'),
    opts=None,
    capacity_providers=["FARGATE"]    
)


"""
TODO: Extract that task_definition as method, and call for each task definition created to avoid code duplication
"""

locust_master_task_definiton = ecs.TaskDefinition(
    resource_name=format_resource_name(name='slave-eu-west-1'),
    opts=None,
    container_definitions=json_as_string_from_file('locust-master.json'),
    family=f'{pulumi.get_stack()}-locust-master',
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    execution_role_arn="arn:aws:iam::918040319999:role/ecsTaskExecutionRole",
    requires_compatibilities=[
        "FARGATE"
    ]
) 


locust_slave_task_definiton = ecs.TaskDefinition(
    resource_name=format_resource_name(name='eu-west-1'),
    container_definitions=json_as_string_from_file('locust-slave.json'),
    family=f'{pulumi.get_stack()}-locust-slave',
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    execution_role_arn="arn:aws:iam::918040319999:role/ecsTaskExecutionRole",
    requires_compatibilities=[
        "FARGATE"
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[locust_master_task_definiton]        
    )

) 

"""
TODO: Extract that Service as method, and call for each service created to avoid code duplication
"""

locustMasterService = ecs.Service(
    cluster=ecs_cluster.arn,
    resource_name=format_resource_name(name='master-eu-west-1'),
    task_definition=locust_master_task_definiton.arn,
    network_configuration={
        "security_groups" : ["sg-0eae5b78fc45c4b24"],        
        "subnets" : ["subnet-0409a0a361e0101ad"],
        "assign_public_ip": True
    },
    launch_type="FARGATE",
    desired_count=1,
    service_registries={
        "registry_arn" : config.require('service_discovery_arn') #arn:aws:servicediscovery:eu-west-1:918040319999:service/srv-bcipe6i2rdsnkgaz"
    },
    opts=pulumi.ResourceOptions(
        ignore_changes=["resource_name"]
    )


)

locustSlaveService = ecs.Service(
    cluster=ecs_cluster.arn,
    resource_name=format_resource_name(name='slave-eu-west-1'),
    task_definition=locust_slave_task_definiton.arn,
    network_configuration={
        "security_groups" : ["sg-0eae5b78fc45c4b24"],        
        "subnets" : ["subnet-0409a0a361e0101ad"],
        "assign_public_ip": True
    },
    launch_type="FARGATE",
    desired_count=config.require('replicas'),
    opts=pulumi.ResourceOptions(
        depends_on=[locustMasterService]
    ),

)






