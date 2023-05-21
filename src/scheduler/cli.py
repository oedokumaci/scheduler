"""Command line application module."""

import typer

from scheduler.config import YAML_CONFIG
from scheduler.path import LOGS_DIR
from scheduler.utils import check_log_file_name, init_logger

app = typer.Typer()

# Define command line arguments and options
log_file_name_argument = typer.Argument(
    YAML_CONFIG.log_file_name,
    help="Name of the log file. Default can be changed in config.yaml.",
)
override_option = typer.Option(False, help="Override the log file if it exists.")


@app.command()
def main(
    log_file_name: str = log_file_name_argument, override: bool = override_option
) -> None:
    """CLI for scheduler."""

    # Check if log file exists, if so ask to overwrite
    log_file = LOGS_DIR / log_file_name
    if not override and log_file.exists():
        check_log_file_name(log_file_name)

    # Initialize logger
    init_logger(log_file_name)

    # Print log file path
    print("")
    print(f"logs are saved to {log_file.resolve()}")
