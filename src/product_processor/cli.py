import asyncio

import click

import product_processor.processor as pp_processor

processor = pp_processor.Processor()


@click.group()
def pp():
    pass


@pp.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.argument("steps", type=click.Choice(processor.PIPELINE_STEPS.keys()))
def detect(input_file, output_file, steps=""):
    """
    Run the product processing pipeline.
    """

    step_list = [s.strip() for s in steps.split(",") if s.strip()]

    if not step_list:
        raise click.UsageError("No steps provided.")

    asyncio.run(processor.async_detect(input_file, output_file, step_list))


def run():
    """Entry point for console script."""
    pp()
