import pulumi_aws as aws
import pulumi

def vpc_setup(tags: dict):
  azs = aws.get_availability_zones(state="available").names
  two_azs = [azs[0], azs[1]]
  vpc_cidr = "10.0.0.0/16"
  public_subnet_cidr = ["10.0.0.0/24", "10.0.1.0/24"]
  private_subnets_cidr = ["10.0.2.0/24", "10.0.3.0/24"]
  database_subnet_cidr = ["10.0.4.0/24", "10.0.5.0/24"]

  vpc = aws.ec2.Vpc(
    "main", 
    cidr_block=vpc_cidr,
    tags = tags
    )
  
  public_subnets = create_subnets(vpc.id, two_azs, public_subnet_cidr, "public")
  database_subnets = create_subnets(vpc.id, two_azs, database_subnet_cidr, "database")
  private_subnets = create_subnets(vpc.id, two_azs, private_subnets_cidr, "private")

  internet_gateway = aws.ec2.InternetGateway(
    "internet-gateway", 
    vpc_id=vpc.id,
    tags=tags
  )

  nat_eip = aws.ec2.Eip("natgw-eip", domain="vpc")

  nat_gateway = aws.ec2.NatGateway("nat-gateway",
    allocation_id=nat_eip.id,
    subnet_id=public_subnets[0].id,
    tags={
        "Name": "nat-gateway",
        "Environment": tags["Environment"],
        "Project": tags["Project"]
    },
    opts = pulumi.ResourceOptions(depends_on=[internet_gateway])
  )

  public_route_table = aws.ec2.RouteTable("public-route-table",
    vpc_id=vpc.id,
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": internet_gateway.id,
        }
    ],
    tags={
        "Name": "public-route-table",
        "Environment": tags["Environment"],
        "Project": tags["Project"]
    })
  
  private_route_table = aws.ec2.RouteTable("private-route-table",
    vpc_id=vpc.id,  
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": nat_gateway.id
        }
    ],
    tags={
        "Name": "private-route-table",
        "Environment": tags["Environment"],
        "Project": tags["Project"]
    })
  
  database_route_table = aws.ec2.RouteTable("database-route-table",
    vpc_id=vpc.id,  
    routes=[
        {
            "cidr_block": f"{vpc_cidr}",
            "gateway_id": "local"
        }
    ],
    tags={
        "Name": "database-route-table",
        "Environment": tags["Environment"],
        "Project": tags["Project"]
    })

  # public routes association

  for i, subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(
        f"public-route-table-association-{i}",
        subnet_id=subnet.id,
        route_table_id=public_route_table.id,
    )
  
  # database routes association
  # database subnets do not have route to igw/nat gateway
  for i, subnet in enumerate(database_subnets):
    aws.ec2.RouteTableAssociation(
        f"database-route-table-association-{i}",
        subnet_id=subnet.id,
        route_table_id=database_route_table.id,
    )
  
  # private routes association
  for i, subnet in enumerate(private_subnets):
    aws.ec2.RouteTableAssociation(
        f"private-route-table-association-{i}",
        subnet_id=subnet.id,
        route_table_id=private_route_table.id,
    )

  # Create Subnet Group

  db_subnet_group = aws.rds.SubnetGroup("db-subnet-group",
    name="db-subnet-group",
    subnet_ids=[subnet.id for subnet in database_subnets],
    tags={
        "Name": "db-subnet-group",
        "Environment": tags["Environment"],
        "Project": tags["Project"]
    }
  )

  return {
    "vpc": vpc,
    "public_subnets": public_subnets,
    "private_subnets": private_subnets,
    "database_subnets": database_subnets,
    "internet_gateway": internet_gateway,
    "public_route_table": public_route_table
  }


def create_subnets(vpc_id: str, availability_zones: str, cidr_block: str, name: str):
  """
  Create public subnets in the specified availability zones. based on /16 CIDR block.
  """
  subnets = []
  for i, cidr in enumerate(cidr_block):
      subnet = aws.ec2.Subnet(
          f"{name}-subnet-{i}",
          vpc_id=vpc_id,
          cidr_block=cidr,
          availability_zone=availability_zones[i],
          tags={
             'Name': f"{name}-subnet-{'A' if i == 0 else 'B'}",
          }
      )
      subnets.append(subnet)
  return subnets