import logging
import random
from functools import cached_property

from scheduler.exam_proctor import Exam, Proctor


class Planner:
    def __init__(self, exams: list[Exam], proctors: list[Proctor]) -> None:
        """
        Initialize the Planner class.

        Args:
            exams (list[Exam]): A list of Exam objects.
            proctors (list[Proctor]): A list of Proctor objects.
        """
        self.exams = exams
        self.proctors = proctors
        self.min_duties: int = 0
        self.max_duties: int = 0
        self.blocks: dict[str, list[Exam]] = {}

    @cached_property
    def max_total_proctored_before(self) -> int:
        """
        Get the maximum number of duties proctors have had before the scheduling process.

        Returns:
            int: The maximum number of duties proctors have had before the scheduling process.
        """
        return max([proctor.total_proctored_before for proctor in self.proctors])

    def reset_all(self) -> None:
        for exam in self.exams:
            exam.reset()
        for proctor in self.proctors:
            proctor.reset()

    def set_min_max_duties(self) -> None:
        """
        Calculate and set the minimum and maximum number of duties per proctor.
        """
        total_proctors_needed = sum(
            [exam.number_of_proctors_needed for exam in self.exams]
        )
        self.min_duties = total_proctors_needed // len(self.proctors)
        self.max_duties = self.min_duties + 1
        logging.info(f"min_duties: {self.min_duties}, max_duties: {self.max_duties}")

    def set_blocks(self) -> None:
        """
        Set the blocks attribute and sort exams within blocks based on priority.
        """
        # The order in list of exams for each block should be as follows:
        # 1. Exams that require a specific proctor
        # 2. Exams that require a PhD proctor
        # 3. Rest of the exams
        self.exams.sort(
            key=lambda exam: 1
            if exam.requires_specific_proctor
            else 2
            if exam.requires_phd_proctor
            else 3,
        )

        for exam in self.exams:
            if exam.block not in self.blocks:
                self.blocks[exam.block] = []
            self.blocks[exam.block].append(exam)

    def ordered_blocks_keys(self, most_needed_to_least: bool = True) -> list[str]:
        """
        Get a list of block keys, ordered by:
        1. the number of exams that require a specific proctor,
        2. the number of proctors needed for the block.

        Args:
            most_needed_to_least (bool, optional): Whether to order the blocks from most needed to least needed. Defaults to True.

        Returns:
            list[str]: A list of block keys.
        """
        blocks_keys = list(self.blocks.keys())
        number_of_proctors = len(self.proctors)
        blocks_keys.sort(
            key=lambda block: sum(
                [
                    exam.number_of_proctors_needed
                    if not exam.requires_specific_proctor
                    else number_of_proctors
                    for exam in self.blocks[block]
                ]
            ),
            reverse=most_needed_to_least,
        )
        return blocks_keys

    def get_available_proctors(
        self, exam: Exam, all_constraints: bool = True
    ) -> list[Proctor]:
        """
        Get a list of available proctors for an exam.

        Args:
            exam (Exam): An Exam object.
            all_constraints (bool, optional): Whether to use all constraints. Defaults to True.

        Returns:
            list[Proctor]: A list of available Proctor objects.
        """
        available_proctors = []
        for proctor in self.proctors:
            if (
                len(proctor.duties)
                > self.max_duties
                + self.max_total_proctored_before
                - proctor.total_proctored_before
            ):
                continue
            constraints = (
                (proctor.unavailable + proctor.not_preferred).copy()
                if all_constraints
                else proctor.unavailable.copy()
            )
            constraints.extend([duty.block for duty in proctor.duties])
            if exam.block not in constraints:
                if exam.requires_specific_proctor is not None:
                    if proctor.name == exam.requires_specific_proctor.name:
                        available_proctors.append(proctor)
                    else:
                        continue
                elif (
                    exam.requires_phd_proctor
                ):  # this is elif not if assuming that requires_specific_proctor exams need only 1 proctor
                    if proctor.proctor_class == 3:
                        available_proctors.append(proctor)
                    else:
                        continue
                else:
                    available_proctors.append(proctor)
        return available_proctors

    def schedule(self, try_number: int = 1) -> int:
        """
        Schedule exams based on proctor availability.

        Args:
            try_number (int, optional): The number of the scheduling attempt. Defaults to 0.
        """
        self.reset_all()
        for block in self.ordered_blocks_keys():
            available_proctors_for_block = set()
            total_proctors_needed_for_block = 0
            for exam in self.blocks[block]:
                for proct in self.get_available_proctors(exam, all_constraints=False):
                    available_proctors_for_block.add(proct)
                total_proctors_needed_for_block += exam.number_of_proctors_needed
            if len(available_proctors_for_block) < total_proctors_needed_for_block:
                # logging.error(
                #     f"Try {try_number} failed! Not enough proctors for block {block}.\nAvailable proctors: {', '.join([proct.name for proct in available_proctors_for_block])}\nTotal number of Proctors needed: {total_proctors_needed_for_block}"
                # )
                return 1
            for exam in self.blocks[block]:
                available_proctors = self.get_available_proctors(
                    exam, all_constraints=True
                )
                if len(available_proctors) < exam.number_of_proctors_needed:
                    available_proctors = self.get_available_proctors(
                        exam, all_constraints=False
                    )
                min_not_reached = [
                    proctor
                    for proctor in available_proctors
                    if len(proctor.duties)
                    < self.min_duties
                    + self.max_total_proctored_before
                    - proctor.total_proctored_before
                ]
                if len(available_proctors) < exam.number_of_proctors_needed:
                    # logging.error(
                    #     f"Try {try_number} failed! Not enough proctors for {exam.title} in block {exam.block} and classroom {exam.classroom}"
                    # )
                    return 1
                if len(min_not_reached) >= exam.number_of_proctors_needed:
                    # If there are enough proctors that have not reached the minimum number of duties, first fill with them
                    select_from = min_not_reached
                else:
                    select_from = available_proctors
                for proctor in random.sample(
                    select_from, k=exam.number_of_proctors_needed
                ):
                    proctor.duties.append(exam)
                    exam.proctors.append(proctor)
        # logging.info(f"Try {try_number} succeeded!")
        return 0
