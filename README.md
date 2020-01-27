[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new)

# serverless-kit-aws
Serverless kit is a Pulumi template that deploys an AWS stack for website hosting

[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new)

# serverless-kit-aws
Serverless kit is a Pulumi template that deploys an AWS stack for website hosting

## Dependencies

* You need a VPC, subnets and security group created
* You need a service discovery # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-service-discovery.html
  The arn output as pulumi config in our module

Now, you could run module correctly. In ecs.py exist service discovery arn commented to use as pulumi config var.

We have locust-slave.json and locust-master.json as task definition in ECS. 


## Docker Directory:

Inside the docker directory we find all the necessary files to build the locust image, both the master and the slave. They are separated into two levels with their docker-compose.yml.

This is because they are different services, if we need to scale the slaves, do not do the same with master. It would not make sense.

The locustfile.py is the file that locust understands to perform the tests. Due to the nature of fargate and the serverless context, we cannot add a file since we don't know the file system beforehand. So when we build the docker image, we add the file with its cases to test. Then through an environment variable, we pass the url we want to test:

```
ATTACKED_HOST
```

The ecs_params.yml file is the task definition file in ECS.

All files that exist in the docker directory, except Dockerfile and locustfile.py are necessary if we want to create an ECS cluster from the aws CLI. They are not necessary for the Pulumi module.


## ECS Pulumi

Previously we need a VPC, subnets and security group to assign to the ECS module:

* security_group
* subnets
* vpc_id

To be able to communicate with the different services that we have deployed in ECS with the Fargate type, we need a service discovery for it. The ECS module already takes it into account but we have to send by configuration the names of the private DNS and the service discovery.

* private_dns_name -> Route 53
* service_discovery_name -> Service Discovery

On the other hand, we have the templates of the Fargate containers for master and slave.

Locust-master.json example:

```
  "name": "locust-master",
  "image": "rmrbest / locust",
  "cpu": 1,
  "memory": 256,
  "essential": true,
  "portMappings": [
```

In this part we indicate the image that we have created from the docker directory and the name. In addition to the limits of cpu and memory that we consider.

It currently points to the docker hub but can be in ECR or any other repository.

Environment

```
 "environment": [
    {
      "name": "ATTACKED_HOST",
      "value": "https://nuage.studio"
    },
    {
      "name": "LOCUST_MODE",
      "value": "master"
    },
    {
      "name": "LOCUST_MASTER_BIND_PORT",
      "value": "5557"
    },
    {
      "name": "TASK_DELAY",
      "value": "1000"
    },
    {
      "name": "QUIET_MODE",
      "value": "$ {QUIET_MODE: -false}"
    }
  ],
```

Basically what we have in the docker-compose.yml file of the docker directory that we refer to the environment variables in this file.

The target URL and that locustfile.py will implicitly collect to launch the tests (it is necessary to see if from locustfile.py it can be indicated, I have not seen it). This fargate contender will act in the context of Locust, in this case as a master. Then the port to which the slaves will connect.

We can find the use of this file in ecs.py:

 container_definitions = json_as_string_from_file ('locust-master.json'),


Let's go to the locust-slave.json file:

It is very similar to the locust-master.json file but we will not stop in this part of environment variables and specifically in the LOCUST_MASTER variable:

```
  {
      "name": "LOCUST_MASTER",
      "value": "locust-master.locust"
    },
```

The value of this refers to the entry in the dns created by the module service discovery:

```
ecs.py:

    name = config.require ('service_discovery_name'),
    namespace_id = private_dns_namespace.id,
```

Once created, you can go to check Route53. It is important that it coincides since otherwise the locust slaves cannot connect to the master.




 




