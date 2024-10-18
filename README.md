# pipeline

A minimal RESTful API that allows users to set up and manage a simple CI/CD pipeline
configuration.

## Assumptions

1. The service is only responsible for triggering the stages, not managing their execution.

2. It supports either sequential or parallel scheduling of stages but does not resolve any
   DAG (Directed Acyclic Graph) of dependent stages. All stages are scheduled either
   sequentially or in parallel.

3. In the case of sequential scheduling, stages execute in the order they appear in the
   input data (e.g., `Run`, `Build`, `Deploy`). For parallel scheduling, the order does not
   matter.

4. By default, stages are scheduled sequentially in the order they appear in the input data.

5. If a pipeline fails, the entire pipeline must be retried. There is no support for
   retrying individual stages of an existing pipeline.

6. Each stage must have a unique name within a pipeline configuration. If two stages share
   the same name, a validation error will occur.

7. Validating Dockerfiles or Kubernetes manifests before execution is non-trivial, so this
   demo service does not perform any such validation.

8. The data structure used to store the pipeline configuration in memory is
   concurrency-safe, ensuring that concurrent calls to the service do not corrupt the data.
