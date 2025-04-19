from pulumi_aws import ec2 

web_server_security_group = ec2.SecurityGroup("web-sg",
    description="Enable HTTP access",
    vpc_id="vpc-0e519291d11e7d07a",  # Replace with your VPC ID
    tags={"Name": "web-sg"},
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": [
                "0.0.0.0/0",  # Allow HTTP access from anywhere 
            ],
        },
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }  # Allow all outbound traffic    
    ]  
)