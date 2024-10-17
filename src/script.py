# d = {
#     "name": "CI Pipeline",
#     "git_repository": "https://github.com/example/repo",
#     "stages": [
#         {
#             "type": "Run",
#             "name": "Run tests",
#             "command": "pytest",
#             "timeout": 500,
#         },
#         {
#             "type": "Build",
#             "name": "Build Docker image",
#             "dockerfile": "FROM alpine:latest && CMD ['echo', 'Hello, World!']",
#             "tag": "latest",
#             "ecr_repository": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
#         },
#         {
#             "type": "Deploy",
#             "name": "deploy-app-stage",
#             "k8s_manifest": {
#                 "apiVersion": "apps/v1",
#                 "kind": "Deployment",
#                 "metadata": {"name": "my-app"},
#                 "spec": {
#                     "replicas": 2,
#                     "selector": {"matchLabels": {"app": "my-app"}},
#                     "template": {
#                         "metadata": {"labels": {"app": "my-app"}},
#                         "spec": {
#                             "containers": [
#                                 {
#                                     "name": "my-app-container",
#                                     "image": "my-app-image:v1.0.0",
#                                     "ports": [{"containerPort": 80}],
#                                 }
#                             ]
#                         },
#                     },
#                 },
#             },
#             "cluster": {
#                 "name": "my-cluster",
#                 "server_url": "https://my-cluster.example.com",
#                 "namespace": "production",
#             },
#         },
#     ],
#     "parallel": True,
# }

# from src.dto import Pipeline

# pipeline = Pipeline(**d)

# print(pipeline.model_dump())
