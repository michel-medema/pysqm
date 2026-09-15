# PySQM

Running experiments on an HPC cluster requires splitting the experiments up into jobs, submitting these jobs, and managing all the results. Ideally, the jobs should be short to minimise the chance of failure and to maximise the amount of work that can be performed in parallel. The entire process can easily become quite difficult to manage, however, as jobs may fail for various reasons, and sometimes it is necessary to repeat parts of the experiments because the code or data changes. Instead of running all the jobs again, ideally, only those that are affected should be resubmitted, but selecting exactly those jobs is often impractical.

This Python package provides a queue manager that automatically manages the submission of jobs on an HPC cluster that uses Slurm. Given a list of jobs, the queue manager submits them based on the available capacity in the queue (often, users have a specific number of jobs that can be in the queue at any given point in time). It also filters out jobs that are already in the queue or for which output files already exist. This way, it makes it easier to resubmit certain jobs: simply provide all the jobs to the queue manager, and it will determine which jobs need to be resubmitted based on the state of the queue and the available output files. If jobs need to be rerun that were previously executed successfully, the corresponding output files can simply be deleted to ensure that those jobs are submitted again.

## Usage

The Git repository of this package can be added as a dependency to the Python project. When using Poetry, for example, you can use this package by adding the following dependency to the `pyproject.toml` file:

```
pysqm @ git+https://github.com/michel-medema/pysqm.git@v0.1.0
```

In your project, you have to create a list of jobs by specifying the job script, Slurm options, and output file. Then, you create the queue manager and pass it the list of jobs. The queue manager will then manage the rest of the process. If the queue is full, it will periodically check the queue for available capacity and submit additional jobs based on this capacity. Once all the jobs have been submitted, the queue manager will return.

Jobs can be configured using the regular Slurm options such as the number of tasks, CPUs per task, etc. When using the `FileBasedSlurmJob`, you can also specify the absolute path to the output file. The queue manager will check if it already exists, and if so, skip that job. If your jobs do not have output files, you can use the more general `SlurmJob` job type. Additional subclasses can also be created, for instance, when results are stored elsewhere and the check for this part requires custom logic.

Below is a minimal example of how to use the queue manager:

```
from pysqm.jobs import SlurmOptions, FileBasedSlurmJob
from pysqm.queue_manager import SlurmQueueManager


# Create a list with all the jobs.
jobs: list[SlurmJob] = []

# A job should have a unique name, specify the path to the job script,
# specify the list of arguments that should be passed to the job script,
# define all the Slurm options, and specify the absolute path to the output file.
job = FileBasedSlurmJob(job_name, path_to_job_script, script_arguments, SlurmOptions(...), output_path)

# Naturally, the job list can be created in a loop.
jobs.append(job)

# Instantiate the queue manager and call submit.
SlurmQueueManager().submit(jobs)
```

### Parameters

The following table provides an overview of the constructor arguments accepted by the queue manager. All values have reasonable default values that should work in most cases.

| Parameter           | Type  | Default  | Description                                                                                                                                                                                                    |
|:--------------------|:------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| max_parallel_jobs   | int   | 1000     | The maximum number of jobs that can be in the queue at any point in time.                                                                                                                                      |
| timeout             | int   | 30000    | The amount of time that the queue manager waits (in milliseconds) before checking the queue again for available capacity if not all jobs can be submitted at the first attempt.                                |
| retries             | int   | 3        | The number of times the queue manager will try to submit a job if the job fails to submit (note that this does not apply to a job that starts running and then fails; only when the slurm submit itself fails. |