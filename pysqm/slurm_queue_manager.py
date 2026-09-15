import subprocess
import time

from pysqm.slurm_job import SlurmJob


class SlurmQueueManager:
    def __init__(self, max_parallel_jobs: int = 1000, timeout: int = 30000, retries: int = 3):
        if not isinstance(max_parallel_jobs, int) or max_parallel_jobs < 1:
            raise ValueError("The maximum number of parallel jobs should be an integer with a value of at least 1.")

        if not isinstance(timeout, int) or timeout < 1000:
            raise ValueError("The timeout should be an integer with a value of at least 1000 milliseconds.")

        if not isinstance(retries, int) or retries < 0:
            raise ValueError("The number of retries should be an integer and cannot be smaller than zero.")

        self.max_parallel_jobs: int = max_parallel_jobs

        # Convert the timeout from milliseconds to seconds.
        self.timeout: float | int = timeout / 1000.0

        self.retries: int = retries

    def get_available_capacity(self) -> int:
        """
        Determine the available capacity of the queue. This value is equal to the number of jobs that can
        still be submitted until the maximum number of parallel jobs is reached. It can be negative if the length of
        the queue exceeds the specified maximum number of parallel jobs.

        :return: The available capacity of the queue.
        """
        return self.max_parallel_jobs - len(get_jobs_in_queue())

    def submit(self, jobs: list[SlurmJob]):
        # Remove jobs that are already in the queue or whose results are already available (because it was submitted previously).
        queued_jobs: list[str] = get_jobs_in_queue()
        remaining_jobs: list[SlurmJob] = [job for job in jobs if job.name not in queued_jobs and not job.results_available()]

        print(f"Skipping {len(jobs) - len(remaining_jobs)} jobs because they are already in the queue or their results are already available.")

        # Retries is larger or equal to zero, so adding one ensures that this loop runs at least once (since the end of the range is exclusive).
        for retry in range(0, self.retries + 1):
            failed_jobs: list[SlurmJob] = []
            next_job_idx: int = 0

            # Try to submit all jobs in the list before retrying any failed jobs.
            while next_job_idx < len(remaining_jobs):
                # Wait specified time before submitting more jobs if this is not the very first iteration.
                if retry > 0 or next_job_idx > 0:
                    time.sleep(self.timeout)

                num_jobs: int = len(remaining_jobs) - next_job_idx
                capacity: int = self.get_available_capacity()

                print(
                    f"{num_jobs} job(s) remaining. Submitting {max(0, min(capacity, num_jobs))} more based on available capacity.")

                failed: int = 0

                # Submit jobs until either the maximum capacity or the end of the job list has been reached.
                while capacity > 0 and next_job_idx < len(remaining_jobs):
                    job = remaining_jobs[next_job_idx]

                    if job.submit():
                        # Job submitted successfully. Lower available capacity by one.
                        capacity -= 1
                    else:
                        # Submission failed. Store job so that it can be retried later.
                        failed_jobs.append(job)
                        failed += 1

                    # Move to the next job in the list.
                    next_job_idx += 1

                if failed > 0:
                    print(
                        f"Failed to submit {failed} jobs. These will be resubmitted {self.retries - retry} more times.")

            # At this point, all the jobs have been processed. If none failed, there is no more work to be done.
            if len(failed_jobs) < 1:
                print(f"All jobs have been submitted.")
                return

            # If there are failed jobs, these will be retried.
            remaining_jobs = failed_jobs

        print(f"Failed to submit {len(remaining_jobs)} jobs after the maximum number of retries. Exiting.")


def get_jobs_in_queue() -> list[str]:
    queue_list = subprocess.run(["squeue", "--me", "--noheader", "--array", "--states=all", "--format=%j"], text=True, capture_output=True)

    if queue_list.returncode == 0:
        return queue_list.stdout.splitlines()
    else:
        return []
