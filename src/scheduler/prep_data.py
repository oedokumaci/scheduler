import logging

import pandas as pd

from scheduler.config import YAMLConfig
from scheduler.exam_proctor import Exam, Proctor
from scheduler.path import INPUTS_DIR


class Parser:
    def __init__(self, config: YAMLConfig) -> None:
        """
        Initialize the Parser class.

        Args:
            config (YAMLConfig): The YAML configuration object.
        """
        self.config = config
        self.exams_df: None | pd.DataFrame = None
        self.proctors_df: None | pd.DataFrame = None

    def read_excels(self) -> None:
        """
        Read the input Excel files and store the dataframes.
        """
        self.exams_df = pd.read_excel(INPUTS_DIR / self.config.exams_file)
        self.proctors_df = pd.read_excel(INPUTS_DIR / self.config.proctors_file)
        logging.info("Successfully read input Excel files.")

    def clean_exams_df(self) -> None:
        """
        Clean the exams dataframe.
        """
        if self.exams_df is None or self.proctors_df is None:
            raise ValueError("Dataframes are not initialized.")

        # Replace blank spaces in column names with underscores
        self.exams_df.columns = self.exams_df.columns.str.replace(" ", "_")

        # Get columns to be filled, which are the first 5 columns
        df_fill_nan_columns = self.exams_df.columns[:5]

        # Fill missing values using forward fill method
        for col in df_fill_nan_columns:
            self.exams_df[col] = self.exams_df[col].fillna(method="ffill")

        self.exams_df.loc[self.exams_df["Classrooms"].isna()]

        # Convert Exam_Date column to string
        self.exams_df["Exam_Date"] = self.exams_df["Exam_Date"].astype(str)

    def clean_proctors_df(self) -> None:
        """
        Clean the proctors dataframe.
        """
        if self.exams_df is None or self.proctors_df is None:
            raise ValueError("Dataframes are not initialized.")

        # Replace blank spaces in column names with underscores
        self.proctors_df.columns = self.proctors_df.columns.str.replace(" ", "_")

        # Convert Total_Proctored_Before and Proctor_Class columns to int
        self.proctors_df["Total_Proctored_Before"] = self.proctors_df[
            "Total_Proctored_Before"
        ].astype(int)
        self.proctors_df["Proctor_Class"] = self.proctors_df["Proctor_Class"].astype(
            int
        )

    def parse_exams(self) -> list[Exam]:
        """
        Parse the exams dataframe and return a list of Exam objects.

        Returns:
            list[Exam]: A list of Exam objects.
        """
        if self.exams_df is None:
            raise ValueError("Exams dataframe is not initialized.")

        exams = []
        last_exam = ""

        for row in self.exams_df.itertuples():
            try:
                classrooms = row.Classrooms.split("|")
                for classroom in classrooms:
                    exams.append(
                        Exam(
                            row.Exam_Title,
                            row.Exam_Date,
                            row.Reserved_Slots,
                            classroom,
                            row.Instructors,
                        )
                    )
                last_exam = row.Exam_Title
            except AttributeError as e:
                # If there are multiple instructors making Classrooms is NaN
                if last_exam == row.Exam_Title:
                    # Find all exams with the same title, date, and time
                    find_all_exams = [
                        exam
                        for exam in exams
                        if exam.title == row.Exam_Title
                        and exam.date == row.Exam_Date
                        and exam.time == row.Reserved_Slots
                    ]
                    # Append instructors to existing exams
                    for exam in find_all_exams:
                        exam.instructor += f", {row.Instructors}"
                else:
                    raise e

        return exams

    def parse_proctors(self) -> list[Proctor]:
        """
        Parse the proctors dataframe and return a list of Proctor objects.

        Returns:
            list[Proctor]: A list of Proctor objects.
        """
        if self.proctors_df is None:
            raise ValueError("Proctors dataframe is not initialized.")

        proctors = []

        for row in self.proctors_df.itertuples():
            proctors.append(
                Proctor(
                    row.Name,
                    row.Email,
                    row.Total_Proctored_Before,
                    row.Proctor_Class,
                )
            )

        return proctors

    def parse(self) -> tuple[list[Exam], list[Proctor]]:
        """
        Parse data and return a tuple of Exam and Proctor objects.

        Returns:
            tuple[list[Exam], list[Proctor]]: A tuple of Exam and Proctor objects.
        """
        self.read_excels()
        self.clean_exams_df()
        self.clean_proctors_df()
        exams = self.parse_exams()
        proctors = self.parse_proctors()
        return exams, proctors


class Prepper:
    def __init__(
        self, exams: list[Exam], proctors: list[Proctor], config: YAMLConfig
    ) -> None:
        """
        Initialize the Prepper class.

        Args:
            exams (list[Exam]): A list of Exam objects.
            proctors (list[Proctor]): A list of Proctor objects.
        """
        self.exams = exams
        self.proctors = proctors
        self.config = config

    def auto_add_constraints(self) -> None:
        """
        Automatically add constraints to proctors using exams.
        """
        first_year_ma_proctors = [
            proctor for proctor in self.proctors if proctor.proctor_class == 1
        ]
        second_year_ma_proctors = [
            proctor for proctor in self.proctors if proctor.proctor_class == 2
        ]

        for exam in self.exams:
            if exam.is_first_year_masters_exam:
                for proctor_one in first_year_ma_proctors:
                    proctor_one.unavailable.append(exam.block)
            elif exam.is_second_year_masters_exam:
                for proctor_two in second_year_ma_proctors:
                    proctor_two.unavailable.append(exam.block)

    def auto_add_proctor_numbers(self) -> None:
        """
        Automatically add proctor numbers to exams.
        """
        for exam in self.exams:
            if "V-" in exam.classroom:
                exam.number_of_proctors_needed = 2
            else:
                exam.number_of_proctors_needed = 1

    def manually_add_constraints(self) -> None:
        """
        Manually add constraints to proctors using input Excel file.
        """
        df = pd.read_excel(INPUTS_DIR / self.config.proctors_file)
        all_blocks = sorted(list({exam.block for exam in self.exams}))

        for block in all_blocks:
            for row in df[["Name", block]].itertuples():
                for proct in self.proctors:
                    if proct.name == row.Name:
                        proctor = proct
                        break
                else:
                    raise ValueError(
                        f"Proctor {row.Name} not found, check proctors file for a typo."
                    )
                if row[2] == 1:
                    proctor.unavailable.append(block)
                elif row[2] == 2:
                    proctor.not_preferred.append(block)

    def manually_add_proctor_numbers(self) -> None:
        """
        Manually add proctor numbers to exams using input Excel file.
        """
        df = pd.read_excel(INPUTS_DIR / self.config.exams_file_for_proctor_numbers)
        for row in df.itertuples():
            for exa in self.exams:
                if exa.title == row.Exam_Title and exa.classroom == row.Classroom:
                    exam = exa
                    break
            else:
                raise ValueError(
                    f"Exam {row.Exam_Title} in {row.Classroom} not found, check exams file for a typo."
                )
            exam.number_of_proctors_needed = row.Number_of_Proctors_Needed

    def manually_add_specific_proctors(self) -> None:
        """
        Manually add specific proctors to exams.

        This method prompts the user to input specific proctors for exams.
        The user is presented with a list of exams and proctors to choose from.
        The selected exam is updated with the specific proctor.

        Note: Each exam should require exactly 1 proctor.

        Returns:
            None
        """
        user_input = (
            input("Do you want to manually add specific proctors? [Y/n]: ") or "y"
        )
        while user_input.lower() == "y":
            for i, exam in enumerate(self.exams):
                print(
                    f"{i+1}. {exam.title}, {exam.block}, {exam.classroom}, {exam.instructor}"
                )
            exam_selection = int(input("Select an exam from the above list: ")) - 1
            exam = self.exams[exam_selection]
            if exam.number_of_proctors_needed != 1:
                logging.error(
                    "Exam should require exactly 1 proctor, select another exam"
                )
                continue
            print("")
            for i, proctor in enumerate(self.proctors):
                print(f"{i+1}. {proctor.name}")
            proctor_selection = int(input("Select a proctor from the above list: ")) - 1
            proctor = self.proctors[proctor_selection]
            exam.requires_specific_proctor = proctor
            user_input = (
                input("Do you want to add more specific proctors? [Y/n]: ") or "Y"
            )
            if user_input.lower() == "y":
                print("")

    def prepare(self, auto_add: bool) -> None:
        """
        Prepare the data for scheduling.

        Args:
            auto_add (bool): Whether to automatically add constraints and proctor numbers.

        This method prepares the data for scheduling by adding constraints and proctor numbers.
        If auto_add is True, it automatically adds constraints and proctor numbers using predefined rules.
        If auto_add is False, it prompts the user to manually add constraints and proctor numbers.

        Returns:
            None
        """
        if auto_add:
            self.auto_add_constraints()
            self.auto_add_proctor_numbers()
        else:
            self.manually_add_constraints()
            self.manually_add_proctor_numbers()
            self.manually_add_specific_proctors()

    def produce_output_excels(self) -> None:
        """
        Produce output excels containing the scheduled exams and proctors.
        """
        # Create a dataframe for exams
        df_exams = pd.DataFrame(
            [
                [
                    exam.title,
                    exam.block,
                    exam.classroom,
                    exam.instructor,
                    exam.number_of_proctors_needed,
                ]
                for exam in self.exams
            ],
            columns=[
                "Exam_Title",
                "Exam_Block",
                "Classroom",
                "Instructors",
                "Number_of_Proctors_Needed",
            ],
        )

        # Create a dataframe for proctors
        all_blocks = sorted(list({exam.block for exam in self.exams}))
        proctor_data = []
        for proctor in self.proctors:
            unavailable: list[int | str] = []
            for block in all_blocks:
                if block in proctor.unavailable:
                    unavailable.append(1)
                else:
                    unavailable.append("")
            proctor_data.append(
                [
                    proctor.name,
                    proctor.email,
                    proctor.total_proctored_before,
                    proctor.proctor_class,
                ]
                + unavailable
            )

        df_proctors = (
            pd.DataFrame(
                proctor_data,
                columns=["Name", "Email", "Total_Proctored_Before", "Proctor_Class"]
                + all_blocks,
            )
            .sort_values(by=["Proctor_Class", "Name"])
            .reset_index(drop=True)
        )

        # Write dataframes to excel
        df_exams.to_excel(INPUTS_DIR / "Exams.xlsx", index=False)
        df_proctors.to_excel(INPUTS_DIR / "Proctors.xlsx", index=False)
