import json

def container_definition(image: str, region: str, project_name: str, domain_fqdn: str, secret_arn: str):
    container_definition = [
        {
            "name": "fastapi-backend",
            "image": f"{image}",
            "cpu": 1,
            "memory": 512,
            "essential": True,
            "portMappings": [{
                "containerPort": 8000,
                "hostPort": 8000,
            }],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"/ecs/{project_name}/fastapi-backend",
                    "awslogs-region": f"{region}",
                    "awslogs-create-group": "true",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "environment": [
                {"name": "DOMAIN", "value": "localhost"},
                {"name": "ENVIRONMENT", "value": "local"},
                {"name": "PROJECT_NAME", "value": f"{project_name}"},
                {"name": "STACK_NAME", "value": f"{project_name}-backend"},
                {"name": "BACKEND_CORS_ORIGINS", "value": f"http://{domain_fqdn},https://{domain_fqdn}"},
                {"name": "USERS_OPEN_REGISTRATION", "value": "True"},
                {"name": "SMTP_HOST", "value": ""},
                {"name": "SMTP_USER", "value": ""},
                {"name": "SMTP_PASSWORD", "value": ""},
                {"name": "EMAILS_FROM_EMAIL", "value": "info@example.com"},
                {"name": "SMTP_TLS", "value": "True"},
                {"name": "SMTP_SSL", "value": "False"},
                {"name": "SMTP_PORT", "value": "587"}
            ],
            "secrets": [
                {"name": "POSTGRES_SERVER", "valueFrom": f"{secret_arn}:db_endpoint::"},
                {"name": "POSTGRES_PORT", "valueFrom": "5432"},
                {"name": "POSTGRES_DB", "valueFrom": f"{secret_arn}:db_name::"},
                {"name": "POSTGRES_USER", "valueFrom": f"{secret_arn}:db_username::"},
                {"name": "POSTGRES_PASSWORD", "valueFrom": f"{secret_arn}:db_password::"},
                {"name": "SECRET_KEY", "valueFrom": f"{secret_arn}:secret_key::"},
                {"name": "FIRST_SUPERUSER", "valueFrom": f"{secret_arn}:first_superuser::"},
                {"name": "FIRST_SUPERUSER_PASSWORD", "valueFrom": f"{secret_arn}:first_superuser_password::"}
            ]
        }
    ]
    return json.dumps(container_definition)