import pulumi
from pulumi_aws import ecs, servicediscovery
from utils import format_resource_name, json_as_string_from_file

config = pulumi.Config()


# Service discovery
private_dns_namespace = servicediscovery.PrivateDnsNamespace(
    resource_name=format_resource_name(name='eu-west-1'),
    name=config.require('private_dns_name'),
    vpc=config.require('vpc_id')
)

service_discovery = servicediscovery.Service(
    resource_name=format_resource_name(name='eu-west-1'),
    name=config.require('service_discovery_name'),
    namespace_id=private_dns_namespace.id,
    dns_config={
        "dnsRecords" : 
        [ 
            {
                "ttl" : 300,
                "type" : "A"
            }
        ],
        "namespace_id" : private_dns_namespace.id
    },
    health_check_custom_config={
        "failure_threshold" : 1
    }
)



ecs_cluster = ecs.Cluster(
    resource_name=format_resource_name(name='eu-west-1'),
    opts=None,
    capacity_providers=["FARGATE"]    
)

volume = {
    "name" : "locust-storage"
}



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
    ],
    volumes = [
        volume
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
        "security_groups" : [config.require('security_group')], #["sg-0eae5b78fc45c4b24"],        
        "subnets" : [config.require('subnets')], #["subnet-0409a0a361e0101ad"],
        "assign_public_ip": True
    },
    launch_type="FARGATE",
    desired_count=1,
    service_registries={
        "registry_arn" : servicediscovery.arn #arn:aws:servicediscovery:eu-west-1:918040319999:service/srv-bcipe6i2rdsnkgaz"
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
        "security_groups" : [config.require('security_group')],        
        "subnets" : [config.require('subnets')],
        "assign_public_ip": True
    },
    launch_type="FARGATE",
    desired_count=config.require('replicas'),
    opts=pulumi.ResourceOptions(
        depends_on=[locustMasterService]
    ),
)






