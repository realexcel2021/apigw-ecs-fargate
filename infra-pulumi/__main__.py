import pulumi
import pulumi_aws as aws
from resources.vpc import vpc_setup
from resources.secret import create_secret_manager


# set up VPC and subnets

project_tags = {
    "Name": "apigw-ecs-fargate-vpc",
    "Environment": "dev",
    "Project": "fastapi-project"
}

project_vpc = vpc_setup(tags=project_tags)



project_secret = create_secret_manager(
    project_name="fastapi-project",
    db_endpoint="db-endpoint",
    db_name="db-name",
    db_username="db-username",
    db_password="db-password")