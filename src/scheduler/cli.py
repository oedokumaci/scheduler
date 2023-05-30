"""Command line application module."""

import typer
from rich import print as rprint

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
number_of_simulations_argument = typer.Argument(1000, help="Number of simulations.")


@app.command()
def main(
    log_file_name: str = log_file_name_argument,
    override: bool = override_option,
    number_of_simulations: int = number_of_simulations_argument,
) -> None:
    """CLI for scheduler."""
    from scheduler.planner import Planner
    from scheduler.prep_data import Parser, Prepper
    from scheduler.simulator import Simulator

    # Check if log file exists, if so ask to overwrite
    log_file = LOGS_DIR / log_file_name
    if not override and log_file.exists():
        check_log_file_name(log_file_name)

    # Initialize logger
    init_logger(log_file_name)

    parser = Parser(YAML_CONFIG)
    prepper = Prepper(*parser.parse(), YAML_CONFIG)
    prepper.prepare(auto_add=False)

    planner = Planner(prepper.exams, prepper.proctors)
    simulator = Simulator(planner, number_of_simulations)

    simulator.simulate()
    simulator.measure_fairness_all()
    ordered_by_fairness = simulator.order_by_fairness()

    _, _, proctors, blocks = simulator.results[ordered_by_fairness[0]]
    rprint(blocks)

    for proctor in proctors:
        rprint(proctor)

    total_duties = {
        proctor.name: len(proctor.duties) + proctor.total_proctored_before
        for proctor in proctors
    }
    sorted_duties = sorted(total_duties.items(), key=lambda item: item[1])
    for proct, duties in sorted_duties:
        print(f"{proct}: {duties}")

    # Print log file path
    print("")
    rprint(f"logs are saved to {log_file.resolve()}")
