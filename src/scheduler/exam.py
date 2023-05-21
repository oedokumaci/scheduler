import re

FIRST_YEAR_MASTERS_COURSES = [503, 504, 505, 506, 509, 510, 515, 516]


class Exam:
    def __init__(
        self, title: str, date: str, time: str, classroom: str, instructor: str
    ) -> None:
        self.title = title.strip()
        self.date = date.strip()
        self.time = time.strip()
        self.classroom = classroom.strip()
        self.instructor = instructor.strip()

    @property
    def code(self) -> int:
        """Extracts 3 digit course code from title."""
        match_object: None | re.Match = re.search(r"\d{3}", self.title)
        if match_object is None:
            raise ValueError(
                f"Exam title {self.title} does not contain a 3 digit course code."
            )
        else:
            return int(match_object.group())

    @property
    def requires_phd_proctor(self) -> bool:
        """Returns True if exam requires a PhD proctor."""
        return self.code >= 500

    @property
    def is_first_year_masters_exam(self) -> bool:
        """Returns True if exam is for first year masters students."""
        return self.code in FIRST_YEAR_MASTERS_COURSES and "ECON" in self.title

    @property
    def is_second_year_masters_exam(self) -> bool:
        """Returns True if exam is for second year masters students."""
        return (
            self.code >= 500
            and "ECON" in self.title
            and not self.is_first_year_masters_exam
        )

    @property
    def block(self) -> str:
        """Returns the block of the exam."""
        return self.date + " " + self.time

    def __repr__(self) -> str:
        return f"""EXAM: {self.title}, {self.block}, {self.classroom}, {self.instructor}
ATTRIBUTES: 1st Year MA Exam = {self.is_first_year_masters_exam}, 2nd Year MA Exam = {self.is_second_year_masters_exam}, Requires PhD Proctor = {self.requires_phd_proctor}"""
