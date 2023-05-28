import logging
from copy import deepcopy

from scheduler.exam_proctor import Exam, Proctor
from scheduler.planner import Planner
from scheduler.utils import standard_deviation, timer_decorator


class Simulator:
    def __init__(self, planner: Planner, number_of_simulations: int) -> None:
        """
        Initialize the Simulator class.

        Args:
            planner (Planner): An instance of the Planner class.
            number_of_simulations (int): The number of simulations to run.
        """
        self.planner = planner
        self.number_of_simulations = number_of_simulations
        self.results: dict[
            int, tuple[int, list[Exam], list[Proctor], dict[str, list[Exam]]]
        ] = {}
        self.fairness_results: dict[int, tuple[int, float, float, int, int]] = {}

    @timer_decorator
    def simulate(self) -> None:
        """
        Simulate the scheduling process for multiple iterations.
        """
        self.planner.set_min_max_duties()
        self.planner.set_blocks()
        logging.info("Starting Simulations...")
        for i in range(1, self.number_of_simulations + 1):
            # logging.info(f"Starting Simulation {i}...")
            exit_code: int = self.planner.schedule(i)
            self.results[i] = (
                exit_code,
                deepcopy(self.planner.exams),
                deepcopy(self.planner.proctors),
                deepcopy(self.planner.blocks),
            )
            # logging.info(
            #     f"Simulation {i} is completed with {'success' if exit_code == 0 else 'failure'}."
            # )
        logging.info("Simulations Completed.")

    def measure_fairness(self, sim_number: int) -> tuple[int, float, float, int, int]:
        """
        Measure the fairness of a simulation.

        Args:
            sim_number (int): The simulation number.

        Returns:
            tuple[int, float, float, int, int]: Fairness measures, using simulation number as tie breaker.
        """
        failure: int = 0
        if self.results[sim_number][0] != 0:
            failure = 1

        proctors: list[Proctor] = self.results[sim_number][2]
        total_duties = [
            proctor.total_proctored_before + len(proctor.duties) for proctor in proctors
        ]
        standard_deviation_of_total_duties = standard_deviation(total_duties)

        first_year_total_duties = [
            proctor.total_proctored_before + len(proctor.duties)
            for proctor in filter(lambda x: x.proctor_class == 1, proctors)
        ]
        standard_deviation_of_first_year_total_duties = standard_deviation(
            first_year_total_duties
        )

        weak_constraints_not_satisfied = sum(
            not proctor.not_preferred_satisfied() for proctor in proctors
        )

        return (
            failure,
            standard_deviation_of_total_duties,
            standard_deviation_of_first_year_total_duties,
            weak_constraints_not_satisfied,
            sim_number,
        )

    def measure_fairness_all(self) -> None:
        """
        Measure the fairness of all simulations.
        """
        for sim_number in self.results:
            fairness_measure = self.measure_fairness(sim_number)
            self.fairness_results[sim_number] = fairness_measure

    def order_by_fairness(self) -> list[int]:
        """
        Order the simulations by fairness.

        Returns:
            list[int]: The ordered list of simulation numbers.
        """
        return sorted(
            self.fairness_results,
            key=lambda sim_number: min(self.fairness_results[sim_number]),
        )
