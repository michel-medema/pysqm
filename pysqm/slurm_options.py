from dataclasses import dataclass


@dataclass(frozen=True)
class SlurmOptions:
    tasks: int
    cpus_per_task: int
    mem_per_cpu: int
    partition: str
    time: str
    output: str