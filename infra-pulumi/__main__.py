import pulumi
from pulumi_aws import ec2
from securitygroup import web_server_security_group

web_server = ec2.Instance("web-server",
    ami="ami-0c55b159cbfafe1f0",  # Amazon Linux 2 AMI  
    instance_type="t2.micro",
    tags={"Name": "web-server"},
    vpc_security_group_ids=[web_server_security_group.id],
    subnet_id="subnet-023e6010495b6ed8c",  # Replace with your subnet ID
    associate_public_ip_address=True,
    user_data="""#!/bin/bash
        yum update -y  
        yum install -y httpd
        systemctl start httpd
        systemctl enable httpd
        echo "Hello from $(hostname -f)" > /var/www/html/index.html
        """
    )

pulumi.export("instance_id", web_server.id)
pulumi.export("instance_public_ip", web_server.public_ip)

