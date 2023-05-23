import pandas as pd

from scheduler.config import YAMLConfig
from scheduler.exam_proctor import Exam, Proctor
from scheduler.path import INPUTS_DIR


class Parser:
    def __init__(self, config: YAMLConfig) -> None:
        """
        Initialize the Parser class.

        Args:
            config (YAML_CONFIG): The YAML configuration object.
        """
        self.config = config
        self.exams_df: None | pd.DataFrame = None
        self.proctors_df: None | pd.DataFrame = None

    def read_excels(self) -> None:
        """
        Read the input Excel files and store the dataframes.
        """
        if not self.exams_df or not self.proctors_df:
            raise ValueError("Dataframes are not initialized.")

        self.exams_df = pd.read_excel(INPUTS_DIR / self.config.exams_file)
        self.proctors_df = pd.read_excel(INPUTS_DIR / self.config.proctors_file)

    def clean_exams_df(self) -> None:
        """
        Clean the exams dataframe.
        """
        if not self.exams_df or not self.proctors_df:
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
        if not self.exams_df or not self.proctors_df:
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
        if not self.exams_df:
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
        if not self.proctors_df:
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
    def __init__(self, exams: list[Exam], proctors: list[Proctor]) -> None:
        """
        Initialize the Prepper class.

        Args:
            exams (list[Exam]): A list of Exam objects.
            proctors (list[Proctor]): A list of Proctor objects.
        """
        self.exams = exams
        self.proctors = proctors

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

    def prepare(self) -> None:
        """
        Prepare the data for scheduling.
        """
        self.auto_add_constraints()
        self.auto_add_proctor_numbers()

    def produce_output_excels(self) -> None:
        """
        Produce output excels containing the scheduled exams and proctors.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: A tuple of dataframes for exams and proctors.
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
