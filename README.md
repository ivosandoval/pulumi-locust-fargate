[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new)

# serverless-kit-aws
Serverless kit is a Pulumi template that deploys an AWS stack for website hosting

## Dependencies

* You need a VPC, subnets and security group created
* You need a service discovery # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-service-discovery.html
  The arn output as pulumi config in our module

Now, you could run module correctly. In ecs.py exist service discovery arn commented to use as pulumi config var.

We have locust-slave.json and locust-master.json as task definition in ECS. 




