# pipeline

A minimal RESTful API that allows users to set up and manage a simple CI/CD pipeline
configuration.

## Assumptions

-   The service allows sequential or parallel execution of the stages but doesn't resolve
    any DAG (Directed Acyclic Graph) of dependent stages to allow one stage to depend on
    another. All stages either run sequentially or in parallel.

-   In case of sequential execution of stages, order of execution is the same as they appear
    in the input data. The expected order is `Run`, `Build`, and then `Deploy`. Conversely,
    the stage appearance doesn't matter in parallel execution.

-   By default, it'll execute any permutation-combination of the 3 stages in the same order
    as they appear in the input data.

-   If something fails and we need to retry the pipeline, it'll be all or nothing.
    Individual steps of an existing pipeline can't be retried.

-   All stages must have names. Names must be unique within a configuration. Passing two
    stages with the same name will incur a validation error.

-   Validating Dockerfile without attempting to build it is non-trivial, so no validation
    occurs there.

-   The datastructure used to store the pipeline config in memory is concurrency-safe. So
    making concurrent calls won't corrupt it.

##
