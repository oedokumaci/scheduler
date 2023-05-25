"""This module parses and validates the config files in config directory."""
from __future__ import annotations

from typing import TypedDict

import yaml
from pydantic import BaseModel, root_validator, validator

from scheduler.path import CONFIG_DIR


class YAMLConfig(BaseModel):
    """Class that defines the structure and validation rules for the config.yaml file.

    Inherits from pydantic BaseModel.
    """

    # Define the fields for the config file
    log_file_name: str
    exams_file: str
    proctors_file: str
    exams_file_for_proctor_numbers: str

    # Define a validator to ensure the log_file_name is valid
    @validator("log_file_name")
    def log_file_name_must_be_valid(cls, v: str) -> str:
        """Validator to ensure the log_file_name is valid.

        Args:
            v (str): The log_file_name value.

        Raises:
            ValueError: If log_file_name starts with /.
            ValueError: If log_file_name is not a .log or .txt file.

        Returns:
            str: The validated log_file_name.
        """
        if v.startswith("/"):
            raise ValueError(
                f"log_file_name should not start with /, {v!r} starts with /"
            )
        if not v.endswith(".log") and not v.endswith(".txt"):
            raise ValueError(
                f"log_file_name should be a .log or .txt file, {v!r} is not"
            )
        return v

    # Define a validator to ensure the exams_file, proctors_file and exams_file_for_proctor_numbers are valid
    @validator("exams_file", "proctors_file", "exams_file_for_proctor_numbers")
    def file_must_be_valid(cls, v: str) -> str:
        """Validator to ensure the exams_file, proctors_file and exams_file_for_proctor_numbers are valid.

        Args:
            v (str): The exams_file, proctors_file or exams_file_for_proctor_numbers value.

        Raises:
            ValueError: If the file starts with /.
            ValueError: If the file is not a .xlsx file.

        Returns:
            str: The validated exams_file, proctors_file or exams_file_for_proctor_numbers.
        """
        if v.startswith("/"):
            raise ValueError(f"{v!r} should not start with /, {v!r} starts with /")
        if not v.endswith(".xlsx"):
            raise ValueError(f"{v!r} should be a .xlsx file, {v!r} is not")
        return v

    # Define a validator to ensure the exams_file and proctors_file are different
    @root_validator(skip_on_failure=True)
    def exams_and_proctors_files_must_be_different(cls, values: dict) -> dict:
        """Validator to ensure the exams_file and proctors_file are different.

        Args:
            values (dict): The exams_file and proctors_file values.

        Raises:
            ValueError: If exams_file and proctors_file are the same.

        Returns:
            dict: The validated exams_file and proctors_file.
        """
        if values["exams_file"] == values["proctors_file"]:
            raise ValueError(
                f"exams_file and proctors_file should be different, {values['exams_file']!r} and {values['proctors_file']!r} are the same"
            )
        return values


class YAMLConfigDict(TypedDict):
    log_file_name: str
    exams_file: str
    proctors_file: str
    exams_file_for_proctor_numbers: str


def parse_and_validate_configs() -> YAMLConfig:
    """Parse and validate the contents of the config.yaml file.

    Returns:
        YAMLConfig: The validated YAMLConfig object.
    """

    with open(CONFIG_DIR / "config.yaml") as yaml_file:
        # Load the contents of the yaml file into a dictionary
        yaml_config: YAMLConfigDict = yaml.safe_load(yaml_file)

    # Create a YAMLConfig object from the dictionary
    return YAMLConfig(**yaml_config)


# Parse and validate the config files at import time
YAML_CONFIG = parse_and_validate_configs()
