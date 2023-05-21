import pandas as pd
from rich import print as rprint

from scheduler.config import YAML_CONFIG
from scheduler.exam import Exam
from scheduler.path import INPUTS_DIR


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


def main() -> list[Exam]:
    """Main function to process exams.

    Returns:
        list[Exam]: A list of Exam objects.
    """
    # Read exams dataframe from Excel file
    df_exams = pd.read_excel(INPUTS_DIR / YAML_CONFIG.exams_file)

    # Clean the exams dataframe
    cleaned_exams_df = clean_exams_df(df_exams)

    # Get the list of exams
    exams = get_exams(cleaned_exams_df)

    # Print the list of exams using rich library
    rprint(exams)

    return exams


if __name__ == "__main__":
    exams = main()
