import re

FIRST_YEAR_MASTERS_COURSES = [503, 504, 505, 506, 509, 510, 515, 516]


class Exam:
    def __init__(
        self, title: str, date: str, time: str, classroom: str, instructor: str
    ) -> None:
        """Initialize an Exam object.

        Args:
            title (str): The title of the exam.
            date (str): The date of the exam.
            time (str): The time of the exam.
            classroom (str): The classroom for the exam.
            instructor (str): The instructor for the exam.
        """
        self.title = title.strip()
        self.date = date.strip()
        self.time = time.strip()
        self.classroom = classroom.strip()
        self.instructor = instructor.strip()

    @property
    def code(self) -> int:
        """Extracts the 3-digit course code from the title.

        Returns:
            int: The extracted course code.

        Raises:
            ValueError: If the exam title does not contain a 3-digit course code.
        """
        match_object = re.search(r"\d{3}", self.title)
        if match_object is None:
            raise ValueError(
                f"Exam title {self.title} does not contain a 3-digit course code."
            )
        else:
            return int(match_object.group())

    @property
    def requires_phd_proctor(self) -> bool:
        """Check if the exam requires a PhD proctor.

        Returns:
            bool: True if the exam requires a PhD proctor, False otherwise.
        """
        return self.code >= 500

    @property
    def is_first_year_masters_exam(self) -> bool:
        """Check if the exam is for first-year masters students.

        Returns:
            bool: True if the exam is for first-year masters students, False otherwise.
        """
        return self.code in FIRST_YEAR_MASTERS_COURSES and "ECON" in self.title

    @property
    def is_second_year_masters_exam(self) -> bool:
        """Check if the exam is for second-year masters students.

        Returns:
            bool: True if the exam is for second-year masters students, False otherwise.
        """
        return (
            self.code >= 500
            and "ECON" in self.title
            and not self.is_first_year_masters_exam
        )

    @property
    def block(self) -> str:
        """Get the block of the exam.

        Returns:
            str: The block of the exam, represented as a combination of date and time.
        """
        return self.date + " " + self.time

    def __repr__(self) -> str:
        """Return a string representation of the Exam object.

        Returns:
            str: A string representation of the Exam object.
        """
        return f"""EXAM: {self.title}, {self.block}, {self.classroom}, {self.instructor}
ATTRIBUTES: 1st Year MA Exam = {self.is_first_year_masters_exam}, 2nd Year MA Exam = {self.is_second_year_masters_exam}, Requires PhD Proctor = {self.requires_phd_proctor}"""
