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
        self.number_of_proctors_needed: int = 0
        self.requires_specific_proctor: None | Proctor = None
        self.proctors: list[Proctor] = []

    def reset(self) -> None:
        """Reset the Exam object to its initial state."""
        self.proctors = []

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
        attributes = ", ".join(
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}"
            for key, value in self.__dict__.items()
            if key != "proctors" and key != "requires_specific_proctor"
        )
        attributes += f", is_first_year_masters_exam={self.is_first_year_masters_exam}, is_second_year_masters_exam={self.is_second_year_masters_exam}, requires_phd_proctor={self.requires_phd_proctor}"
        proctor_names = [f'"{proctor.name}"' for proctor in self.proctors]
        attributes += f', proctors=[{", ".join(proctor_names)}]'
        attributes += (
            f', requires_specific_proctor="{self.requires_specific_proctor.name}"'
            if self.requires_specific_proctor is not None
            else ""
        )
        return f"{self.__class__.__name__}({attributes})"


class Proctor:
    def __init__(
        self, name: str, email: str, total_proctored_before: int, proctor_class: int
    ) -> None:
        """Initialize a Proctor object.

        Args:
            name (str): The name of the proctor.
            email (str): The email address of the proctor.
            total_proctored_before (int): The total number of exams proctored by the proctor before.
            proctor_class (int): The proctor class of the proctor.

        """
        self.name = name.strip()
        self.email = email.strip()
        self.total_proctored_before = total_proctored_before
        self.proctor_class = proctor_class
        self.unavailable: list[str] = []
        self.not_preferred: list[str] = []
        self.duties: list[Exam] = []

    def reset(self) -> None:
        """Reset the Proctor object to its initial state."""
        self.duties = []

    def __repr__(self) -> str:
        """Return a string representation of the Proctor object.

        Returns:
            str: A string representation of the Proctor object.
        """
        attributes = ", ".join(
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}"
            for key, value in self.__dict__.items()
            if key != "duties"
        )
        attributes += (
            f', duties=[{", ".join([str(exam.code) for exam in self.duties])}]'
        )
        return f"{self.__class__.__name__}({attributes})"
