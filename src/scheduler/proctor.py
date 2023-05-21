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
        self.name = name
        self.email = email
        self.total_proctored_before = total_proctored_before
        self.proctor_class = proctor_class

    def __repr__(self) -> str:
        """Return a string representation of the Proctor object.

        Returns:
            str: A string representation of the Proctor object.
        """
        return f"""PROCTOR: {self.name}, {self.email}, {self.total_proctored_before}, {self.proctor_class}"""
