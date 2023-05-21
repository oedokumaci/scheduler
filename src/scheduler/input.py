import pandas as pd
from rich import print as rprint

from scheduler.config import YAML_CONFIG
from scheduler.exam import Exam
from scheduler.path import INPUTS_DIR
from scheduler.proctor import Proctor


def clean_exams_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the exams dataframe.

    Args:
        df (pd.DataFrame): The exams dataframe to be cleaned.

    Returns:
        pd.DataFrame: The cleaned exams dataframe.
    """
    # Replace blank spaces in column names with underscores
    df.columns = df.columns.str.replace(" ", "_")

    # Get columns to be filled, which are the first 5 columns
    df_fill_nan_columns = df.columns[:5]

    # Fill missing values using forward fill method
    for col in df_fill_nan_columns:
        df[col] = df[col].fillna(method="ffill")

    df.loc[df["Classrooms"].isna()]

    # Convert Exam_Date column to string
    df["Exam_Date"] = df["Exam_Date"].astype(str)

    return df


def clean_proctors_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the proctors dataframe.

    Args:
        df (pd.DataFrame): The proctors dataframe to be cleaned.

    Returns:
        pd.DataFrame: The cleaned proctors dataframe.
    """
    # Replace blank spaces in column names with underscores
    df.columns = df.columns.str.replace(" ", "_")

    # Convert Total_Proctored_Before and Proctor_Class columns to int
    df["Total_Proctored_Before"] = df["Total_Proctored_Before"].astype(int)
    df["Proctor_Class"] = df["Proctor_Class"].astype(int)

    return df


def get_exams(clean_exams_df: pd.DataFrame) -> list[Exam]:
    """Get a list of exams.

    Args:
        clean_exams_df (pd.DataFrame): The cleaned exams dataframe.

    Returns:
        list[Exam]: A list of Exam objects.
    """
    exams = []
    last_exam = ""

    for row in clean_exams_df.itertuples():
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


def get_proctors(clean_proctors_df: pd.DataFrame) -> list[Proctor]:
    """Get a list of proctors.

    Args:
        clean_proctors_df (pd.DataFrame): The cleaned proctors dataframe.

    Returns:
        list[Proctor]: A list of Proctor objects.
    """
    proctors = []

    for row in clean_proctors_df.itertuples():
        proctors.append(
            Proctor(
                row.Name,
                row.Email,
                row.Total_Proctored_Before,
                row.Proctor_Class,
            )
        )

    return proctors


def main() -> tuple[list[Exam], list[Proctor]]:
    """Main function to process exams and proctors.

    Returns:
        list[Exam]: A list of Exam objects.
        list[Exam]: A list of Proctor objects.
    """
    # Read exams and proctors dataframe from Excel files
    df_exams = pd.read_excel(INPUTS_DIR / YAML_CONFIG.exams_file)
    df_proctors = pd.read_excel(INPUTS_DIR / YAML_CONFIG.proctors_file)

    # Clean the exams and proctors dataframes
    cleaned_exams_df = clean_exams_df(df_exams)
    cleaned_proctors_df = clean_proctors_df(df_proctors)

    # Get the list of exams and proctors
    exams = get_exams(cleaned_exams_df)
    proctors = get_proctors(cleaned_proctors_df)

    # Print the list of exams and proctors using rich library
    rprint(exams)
    rprint(proctors)

    return exams, proctors


if __name__ == "__main__":
    exams, proctors = main()
