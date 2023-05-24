import logging
import random

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

    def set_min_max_duties(self) -> None:
        total_proctors_needed = sum(
            [exam.number_of_proctors_needed for exam in self.exams]
        )
        self.min_duties = total_proctors_needed // len(self.proctors)
        self.max_duties = self.min_duties + 1

    def set_blocks(self) -> None:
        """
        Set the blocks attribute.
        """
        # the order in list should be as follows:
        # 1. exam that requires a specific proctor
        # 2. exam that requires a PhD proctor
        # 3. rest of the exams
        self.exams.sort(
            key=lambda exam: exam.requires_specific_proctor.name
            if exam.requires_specific_proctor
            else False,
            reverse=True,
        )
        self.exams.sort(key=lambda exam: exam.requires_phd_proctor, reverse=True)
        for exam in self.exams:
            if exam.block not in self.blocks:
                self.blocks[exam.block] = []
            self.blocks[exam.block].append(exam)

    def ordered_blocks_keys(self, most_needed_to_least: bool = True) -> list[str]:
        """
        Get a list of block keys, ordered by the number of proctors needed for the block.

        Args:
            most_needed_to_least (bool, optional): Whether to order the blocks from most needed to least needed. Defaults to True.

        Returns:
            list[str]: A list of block keys.
        """
        blocks_keys = list(self.blocks.keys())
        blocks_keys.sort(
            key=lambda block: sum(
                [exam.number_of_proctors_needed for exam in self.blocks[block]]
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
            all_constraints (bool, optional): Whether to use all constraints. Defaults to False.

        Returns:
            list[Proctor]: A list of available Proctor objects.
        """
        available_proctors = []
        for proctor in self.proctors:
            if len(proctor.duties) > self.max_duties:
                continue
            constraints = (
                proctor.unavailable + proctor.not_preferred
                if all_constraints
                else proctor.unavailable
            )
            constraints.extend([duty.block for duty in proctor.duties])
            if exam.block not in constraints:
                if exam.requires_specific_proctor is not None:
                    if proctor.name == exam.requires_specific_proctor:
                        available_proctors.append(proctor)
                    else:
                        continue
                if exam.requires_phd_proctor:
                    if proctor.proctor_class == 3:
                        available_proctors.append(proctor)
                    else:
                        continue
                else:
                    available_proctors.append(proctor)
        return available_proctors

    def schedule(self) -> None:
        """
        Schedule exams.
        """
        self.set_min_max_duties()
        self.set_blocks()
        for block in self.ordered_blocks_keys():
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
                    if len(proctor.duties) < self.min_duties
                ]
                if len(available_proctors) < exam.number_of_proctors_needed:
                    logging.error(
                        f"Not enough proctors for {exam.title} in block {exam.block}"
                    )
                    return
                if len(min_not_reached) >= exam.number_of_proctors_needed:
                    select_from = min_not_reached
                else:
                    select_from = available_proctors
                for proctor in random.choices(
                    select_from, k=exam.number_of_proctors_needed
                ):
                    proctor.duties.append(exam)
                    exam.proctors.append(proctor)
