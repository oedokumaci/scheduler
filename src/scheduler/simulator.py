import logging
from copy import deepcopy

from scheduler.exam_proctor import Exam, Proctor
from scheduler.planner import Planner


class Simulator:
    def __init__(self, planner: Planner, number_of_simulations: int) -> None:
        self.planner = planner
        self.number_of_simulations = number_of_simulations
        self.results: dict[
            int, tuple[int, list[Exam], list[Proctor], dict[str, list[Exam]]]
        ] = {}

    def simulate(self) -> None:
        self.planner.set_min_max_duties()
        self.planner.set_blocks()
        for i in range(1, self.number_of_simulations + 1):
            logging.info(f"Starting Simulation {i}...")
            exit_code: int = self.planner.schedule(i)
            self.results[i] = (
                exit_code,
                deepcopy(self.planner.exams),
                deepcopy(self.planner.proctors),
                deepcopy(self.planner.blocks),
            )
            logging.info(
                f"Simulation {i} is completed with {'success' if exit_code == 0 else 'failure'}."
            )
