<div align="left">
  <h1 style="display: inline;">Pipeline</h1>
  <img src="./img/logo.png"
       alt="Pipeline Image"
       style="float: right; width: 128px; height: 128px; margin-left: 10px;">
</div>

A minimal RESTful API that lets you set up and manage a simple CI/CD pipeline configuration.

## Assumptions

1. This assumes that the `pipeline` service is primarily responsible for scheduling the
   stages, not managing their execution. So there's a separate runner module in the `src`
   directory that acts like a task runner. The pipeline service could call the runner via
   RPC, but here it delegates stage execution to the `runner.run_pipeline` function.

2. It supports either sequential or parallel scheduling of stages but doesn’t handle
   resolving any DAG (Directed Acyclic Graph) of dependent stages. All stages are either
   scheduled sequentially or in parallel.

3. In sequential scheduling, stages execute in the order they appear in the input data
   (e.g., `Run`, `Build`, `Deploy`). For parallel scheduling, the order doesn’t matter.

4. By default, stages are scheduled sequentially. But if you pass `parallel: true` during
   pipeline creation, it will schedule the tasks to run in parallel.

5. If a pipeline fails, the entire pipeline has to be retried. There’s no support for
   retrying individual stages within an existing pipeline.

6. Each stage must have a unique name within a pipeline configuration. If two stages share
   the same name, a validation error will occur.

7. The data structure used to store the pipeline configuration in memory is
   concurrency-safe, ensuring that concurrent calls to the service don’t corrupt the data.

## Architecture

Here's a diagram that gives a high-level overview of the service's architecture:

![Architecture diagram][arch-diagram]

-   **POST /pipelines** lets you create a new pipeline from a JSON configuration. It first
    checks if the data is valid, then stores the pipeline in the database.

-   **GET /pipelines/{id}** fetches a pipeline by its ID. It ensures the pipeline exists
    before retrieving it from the database.

-   **PUT /pipelines/{id}** updates an existing pipeline's configuration. It validates the
    new data and updates the pipeline in the database.

-   **DELETE /pipelines/{id}** deletes a pipeline by ID, but only after verifying that the
    pipeline exists. If it does, the pipeline is removed from the database.

-   **POST /pipelines/{id}/trigger** triggers the pipeline's stages, which can run either
    sequentially or in parallel, depending on whether `parallel` is set to `true` or `false`
    during pipeline creation.

The service is written in [Python 3.13], uses [FastAPI] for building the endpoints, and [uv]
for managing the dependencies.

## Prerequisites

-   You can start using the system right away if you have [Docker] installed.
-   To run tests and use the CLI, make sure you have:
    -   [Python 3.13]
    -   [uv]
-   Install [jq] to pretty-print JSON output from API responses.

## Run the service

### Run in a container

From the root directory, run:

```sh
make run-container
```

This will spin up the complete service in a single container and expose it through
`http://localhost:5001`.

### Or, run locally

Once you have Python 3.13 and `uv` installed locally, from the root directory, run:

```sh
make run-local
```

This will create a Python 3.13 virtual environment, install the dependencies, and start a
[uvicorn] server with the application.

## Explore the endpoints

### Via cURL

We'll primarily use `cURL` to interact with the endpoints. Regardless of how you start the
service, it'll be accessible on your local machine via port `5001`.

#### Create a pipeline

To create a new pipeline configuration, make the following request to the `POST /pipelines`
endpoint:

```sh
curl -X 'POST' \
  'http://0.0.0.0:5001/v1/pipelines' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic YWRtaW46YWRtaW4=' \
  -H 'Content-Type: application/json' \
  -d '{
  "git_repository": "https://github.com/example/repo",
  "name": "CI Pipeline",
  "parallel": false,
  "stages": [
    {
      "command": "pytest",
      "name": "Run tests",
      "timeout": 500,
      "type": "Run"
    },
    {
      "dockerfile": "FROM alpine:latest && CMD [\"echo\", \"Hello, World!\"]",
      "ecr_repository": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
      "name": "Build Docker image",
      "tag": "latest",
      "type": "Build"
    },
    {
      "cluster": {
        "name": "my-cluster",
        "namespace": "production",
        "server_url": "https://my-cluster.example.com"
      },
      "k8s_manifest": {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
          "name": "my-app"
        },
        "spec": {
          "replicas": 2,
          "selector": {
            "matchLabels": {
              "app": "my-app"
            }
          },
          "template": {
            "metadata": {
              "labels": {
                "app": "my-app"
              }
            },
            "spec": {
              "containers": [
                {
                  "image": "my-app-image:v1.0.0",
                  "name": "my-app-container",
                  "ports": [
                    {
                      "containerPort": 80
                    }
                  ]
                }
              ]
            }
          }
        }
      },
      "name": "deploy-app-stage",
      "type": "Deploy"
    }
  ]
}' | jq
```

The endpoint uses HTTP basic authentication, so we need to include the username and password
when making the request, both of which are `admin` by default. That's why we add the
base64-encoded header: `-H 'Authorization: Basic YWRtaW46YWRtaW4='`.

Also, notice that we're providing data for all the supported stages: `Run`, `Build`, and
`Deploy`.

This returns (jq pretty-prints the output):

```json
{
  "id": "078ba92d-63fc-4106-b9da-ac2fc6f2cec5",
  "message": "Pipeline created successfully."
}
```

#### Get a pipeline

To fetch the pipeline configuration you just created, extract its ID and pass it to the
`GET` call as follows:

```sh
curl -X 'GET' \
  'http://0.0.0.0:5001/v1/pipelines/078ba92d-63fc-4106-b9da-ac2fc6f2cec5' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic YWRtaW46YWRtaW4=' | jq
```

This will return the stored configuration from the database:

```json
{
  "name": "CI Pipeline",
  "git_repository": "https://github.com/example/repo",
  "stages": [
    {
      "name": "Run tests",
      "type": "Run",
      "command": "pytest",
      "timeout": 500
    },
    {
      "name": "Build Docker image",
      "type": "Build",
      "dockerfile": "FROM alpine:latest && CMD [\"echo\", \"Hello, World!\"]",
      "ecr_repository": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo",
      "tag": "latest"
    },
    {
      "name": "deploy-app-stage",
      "type": "Deploy",
      "cluster": {
        "name": "my-cluster",
        "namespace": "production",
        "server_url": "https://my-cluster.example.com"
      },
      "k8s_manifest": {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
          "name": "my-app"
        },
        "spec": {
          "replicas": 2,
          "selector": {
            "matchLabels": {
              "app": "my-app"
            }
          },
          "template": {
            "metadata": {
              "labels": {
                "app": "my-app"
              }
            },
            "spec": {
              "containers": [
                {
                  "image": "my-app-image:v1.0.0",
                  "name": "my-app-container",
                  "ports": [
                    {
                      "containerPort": 80
                    }
                  ]
                }
              ]
            }
          }
        }
      }
    }
  ],
  "parallel": false,
  "id": "078ba92d-63fc-4106-b9da-ac2fc6f2cec5"
}
```

#### Update a pipeline

To update a pipeline, send the updated configuration along with the pipeline ID:

```sh
curl -X 'PUT' \
  'http://0.0.0.0:5001/v1/pipelines/078ba92d-63fc-4106-b9da-ac2fc6f2cec5' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic YWRtaW46YWRtaW4=' \
  -H 'Content-Type: application/json' \
  -d '{
  "git_repository": "https://github.com/example/repo",
  "name": "CI Pipeline",
  "parallel": true,
  "stages": [
    {
      "command": "pytest",
      "name": "Run tests",
      "timeout": 500,
      "type": "Run"
    }
  ]
}' | jq
```

Here we're updating the pipeline configuration to keep only the `Run` stage and remove the
other two. This returns:

```json
{
  "id": "078ba92d-63fc-4106-b9da-ac2fc6f2cec5",
  "message": "Pipeline updated successfully."
}
```

#### Trigger a pipeline

You can trigger an existing pipeline like this:

```sh
curl -X 'POST' \
  'http://0.0.0.0:5001/v1/pipelines/078ba92d-63fc-4106-b9da-ac2fc6f2cec5/trigger' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic YWRtaW46YWRtaW4=' \
  -d '' | jq
```

This will trigger the pipeline in the background and return:

```json
{
  "id": "078ba92d-63fc-4106-b9da-ac2fc6f2cec5",
  "message": "Pipeline triggered successfully."
}
```

#### Delete a pipeline

Finally, delete the pipeline with the following request:

```sh
curl -X 'DELETE' \
  'http://0.0.0.0:5001/v1/pipelines/078ba92d-63fc-4106-b9da-ac2fc6f2cec5' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic YWRtaW46YWRtaW4=' \
  -d '' | jq
```

This will delete the existing pipeline and cancel it if it's running:

```json
{
  "id": "078ba92d-63fc-4106-b9da-ac2fc6f2cec5",
  "message": "Pipeline deleted successfully."
}
```

### Via OpenAPI docs

You can also interact with the endpoints through the interactive OpenAPI documentation. To
do so, make sure the service is running, then go to [http://localhost:5001/docs][docs] in
your browser. You'll see a page like this:

![FastAPI docs page 1][docs-1]

Clicking on each dropdown will show you an example payload, and you can immediately start
making requests. For example, here’s how to create a pipeline:

![FastAPI docs create pipeline][docs-2]

Clicking the **Execute** button will ask for your credentials. Just use `admin` for both the
username and password. Once that’s done, you can see the request succeeded.

![FastAPI docs create pipeline response][docs-3]

You can explore the other endpoints in a similar fashion.

### Triggering pipelines, inspecting the logs and cancellation behaviors

When you trigger a pipeline, the service prints logs to signal the currently running...

...under construction...

## CLI

The `pipeline` service also provides a simple CLI wrapper over the endpoints, making it easy
to interact with via the command line.

-   **Create a pipeline instance:**

    ```sh
    uv run python -m src.cli create-pipeline --username admin --password admin --data '{
      "git_repository": "https://github.com/example/repo",
      "name": "CI Pipeline",
      "parallel": true,
      "stages": [
        {
          "command": "pytest",
          "name": "Run tests",
          "timeout": 500,
          "type": "Run"
        }
      ]
    }' | jq
    ```

    ```json
    {
      "id": "a0305992-931e-4dc0-aa2b-893116f6542e",
      "message": "Pipeline created successfully."
    }
    ```

-   **Get the pipeline configuration:**

    To retrieve the configuration of the pipeline you just created, use its ID from the
    response above:

    ```sh
    uv run python -m src.cli get-pipeline \
      --username admin \
      --password admin \
      --pipeline-id "a0305992-931e-4dc0-aa2b-893116f6542e" | jq
    ```

    ```json
    {
      "name": "CI Pipeline",
      "git_repository": "https://github.com/example/repo",
      "stages": [
        {
          "name": "Run tests",
          "type": "Run",
          "command": "pytest",
          "timeout": 500
        }
      ],
      "parallel": true,
      "id": "a0305992-931e-4dc0-aa2b-893116f6542e"
    }
    ```

-   **Update the pipeline:**

    ```sh
    uv run python -m src.cli update-pipeline \
      --username admin \
      --password admin \
      --data '{
        "git_repository": "https://github.com/example/repo",
        "name": "CI Pipeline Updated",
        "parallel": false,
        "stages": [
          {
            "command": "pytest",
            "name": "Run tests",
            "timeout": 500,
            "type": "Run"
          }
        ]
      }' \
      --pipeline-id "a0305992-931e-4dc0-aa2b-893116f6542e" | jq
    ```

    ```json
    {
      "id": "a0305992-931e-4dc0-aa2b-893116f6542e",
      "message": "Pipeline updated successfully."
    }
    ```

-   **Trigger the pipeline:**

    ```sh
    uv run python -m src.cli trigger-pipeline \
      --username admin \
      --password admin \
      --pipeline-id "a0305992-931e-4dc0-aa2b-893116f6542e" | jq
    ```

    ```json
    {
      "id": "a0305992-931e-4dc0-aa2b-893116f6542e",
      "message": "Pipeline triggered successfully."
    }
    ```

-   **Delete the pipeline:**

    ```sh
    uv run python -m src.cli delete-pipeline \
      --username admin \
      --password admin \
      --pipeline-id "a0305992-931e-4dc0-aa2b-893116f6542e" | jq
    ```

    ```json
    {
      "id": "a0305992-931e-4dc0-aa2b-893116f6542e",
      "message": "Pipeline deleted successfully."
    }
    ```

## Development & housekeeping

### Run the tests

The tests live in the `tests/` directory and we're using [pytest] to write them. The entire
service is covered by both unit and integration tests. The integration tests are marked with
`pytest.mark.integration` markers.

Unit tests can be run in isolation and don't have any extraneous dependencies. On the
contrary, the integration tests make actual HTTP calls to the the pipeline service, so in
order to run them, the server needs to be up.

Run the unit tests:

```sh
make test
```

This will print:

```txt
---------- coverage: platform darwin, python 3.13.0-final-0 ----------
Name                        Stmts   Miss  Cover
-----------------------------------------------
tests/__init__.py               0      0   100%
tests/test_cli.py              74      0   100%
tests/test_config.py           33      0   100%
tests/test_db.py               46      0   100%
tests/test_dto.py              98      0   100%
tests/test_handlers.py         66      0   100%
tests/test_integration.py      67     43    36%
tests/test_logger.py           38      0   100%
tests/test_main.py             48      2    96%
tests/test_routes.py           45      0   100%
tests/test_runner.py           86      2    98%
tests/test_utils.py            10      0   100%
-----------------------------------------------
TOTAL                         611     47    92%


===================== 73 passed, 5 deselected in 1.59s ===============
```

Run the integration tests while the server is running:

```sh
make run-integration
```

### Linting, formatting, and type checking

[Ruff] is used to lint and format the code, while [mypy] is used for type checking. Run them
with:

```sh
make lint
```

### Dependency management

Dependencies are managed via [uv]. You can add, remove, and update dependencis using the uv
CLI.

## Constraints & limitations

1. During sequential stage execution, if a stage fails, the runner won't run the subsequent
   stages (if any).

2. However, since the service doesn't resolve a DAG of dependent stages, the failure of one
   stage has no effect on other stages during parallel execution.

3. Validating Dockerfiles or Kubernetes manifests before execution is non-trivial, so this
   demo service does not perform such validation. However, it does validate other fields and
   returns HTTP 4xx errors accordingly.

---

<!-- ----------------------------------------------------------------------------------- -->

<!-- Images -->

[arch-diagram]: ./img/arch-diagram.png
[docs-1]: ./img/docs-1.png
[docs-2]: ./img/docs-2.png
[docs-3]: ./img/docs-3.png

<!-- References -->

[docs]: http://localhost:5001/docs
[python 3.13]: https://www.python.org/downloads/release/python-3130/
[fastapi]: https://fastapi.tiangolo.com/
[uv]: https://docs.astral.sh/uv/
[uvicorn]: https://www.uvicorn.org/
[docker]: https://www.docker.com/
[jq]: https://jqlang.github.io/jq/
[pytest]: https://docs.pytest.org/en/stable/
[ruff]: https://docs.astral.sh/ruff/
