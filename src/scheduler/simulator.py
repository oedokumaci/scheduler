import logging
from copy import deepcopy

from scheduler.exam_proctor import Exam, Proctor
from scheduler.planner import Planner
from scheduler.utils import timer_decorator


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
        self.fairness_results: dict[int, list[int]] = {}

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

    def measure_fairness(self, sim_number: int) -> tuple[int, int]:
        """
        Measure the fairness of a simulation.

        Args:
            sim_number (int): The simulation number.

        Returns:
            tuple[int, int]: The fairness measures (diff, weak_constraint_satisfaction).
        """
        if self.results[sim_number][0] != 0:
            return -1, -1
        proctors: list[Proctor] = self.results[sim_number][2]

        min_total_proctor_duties: int = min(
            proctor.total_proctored_before + len(proctor.duties) for proctor in proctors
        )
        max_total_proctor_duties: int = max(
            proctor.total_proctored_before + len(proctor.duties) for proctor in proctors
        )
        diff: int = max_total_proctor_duties - min_total_proctor_duties

        weak_constraint_satisfaction: int
        if all(proctor.not_preferred_satisfied() for proctor in proctors):
            weak_constraint_satisfaction = len(proctors)
        elif all(
            proctor.not_preferred_satisfied()
            for proctor in proctors
            if proctor.proctor_class == 1
        ):
            weak_constraint_satisfaction = len(proctors) - 1
        else:
            weak_constraint_satisfaction = sum(
                proctor.not_preferred_satisfied() for proctor in proctors
            )

        return diff, weak_constraint_satisfaction

    def measure_fairness_all(self) -> None:
        """
        Measure the fairness of all simulations.
        """
        for sim_number in self.results:
            diff, weak_constraint_satisfaction = self.measure_fairness(sim_number)
            if diff == -1 and weak_constraint_satisfaction == -1:
                continue
            self.fairness_results[sim_number] = [diff, weak_constraint_satisfaction]

    def order_by_fairness(self) -> list[int]:
        """
        Order the simulations by fairness.

        Returns:
            list[int]: The ordered list of simulation numbers.
        """
        return sorted(
            self.fairness_results,
            key=lambda sim_number: (
                self.fairness_results[sim_number][
                    0
                ],  # Sort by smallest diff (ascending)
                -self.fairness_results[sim_number][
                    1
                ],  # Sort by higher weak_constraint_satisfaction (descending)
                sim_number,  # Sort by simulation number (ascending) as a tie-breaker
            ),
        )

    def report_fairness(self, first_n: int = 20) -> None:
        """
        Report the fairness measures for all simulations.
        """
        self.measure_fairness_all()
        logging.info(f"Number of Proctors: {len(self.planner.proctors)}")
        ordered_sim_numbers: list[int] = self.order_by_fairness()
        logging.info(
            f"{'Simulation Number':<19}{'Difference':<13}{'Weak Constraint Satisfaction':<27}"
        )
        for sim_number in ordered_sim_numbers[:first_n]:
            diff = self.fairness_results[sim_number][0]
            constraint_satisfaction = self.fairness_results[sim_number][1]
            logging.info(f"{sim_number:<19}{diff:<13}{constraint_satisfaction:<27}")
