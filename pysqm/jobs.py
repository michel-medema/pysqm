import os
import subprocess
from dataclasses import dataclass
from typing import override

from pysqm.options import SlurmOptions


@dataclass(frozen=True)
class SlurmJob:
    name: str
    script: str
    args: list[str]
    options: SlurmOptions

    def submit(self) -> bool:
        args = ["sbatch", f"--ntasks={self.options.tasks}", f"--cpus-per-task={self.options.cpus_per_task}",
                f"--mem-per-cpu={self.options.mem_per_cpu}", f"--partition={self.options.partition}",
                f"--time={self.options.time}", f"--output={self.options.output}", f"--job-name={self.name}",
                self.script] + self.args
        # print(args)

        result = subprocess.run(args)

        return result.returncode == 0

    def results_available(self) -> bool:
        return False

@dataclass(frozen=True)
class FileBasedSlurmJob(SlurmJob):
    output_path: str

    def __post_init__(self):
        if not os.path.isabs(self.output_path):
            raise AttributeError("The output path should be an absolute path.")

        self.args.append(self.output_path)

    @override
    def results_available(self) -> bool:
        return os.path.exists(self.output_path)