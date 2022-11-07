from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template
from typing_extensions import Final

from . import jinja_globals


def main() -> None:
    DESCRIPTION : Final[str] = \
            "Turn a set of files into a standalone ks.cfg. " \
            + "<https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/performing_an_advanced_rhel_9_installation/installation-methods-advanced_installing-rhel-as-an-experienced-user>"
    FILE_HELP : Final[str] = \
            "Path to a file that will be compiled into a " \
            + "kickstart file."

    ARGUMENT_PARSER : Final[ArgumentParser] = ArgumentParser(
            formatter_class=RawDescriptionHelpFormatter,
            description=DESCRIPTION
    )
    ARGUMENT_PARSER.add_argument(
            "file",
            default=Path("ks.cfg.j2"),
            type=Path,
            #required=True  # Do I need this?
            help=FILE_HELP,
            metavar="FILE"
    )
    ARGUMENTS : Final[Namespace] = ARGUMENT_PARSER.parse_args()
    INPUT_FILE_PATH : Final[Path] = ARGUMENTS.file
    jinja_globals.input_file_parent = INPUT_FILE_PATH.parent

    JENV : Final[Environment] = Environment(
            loader=FileSystemLoader(INPUT_FILE_PATH.parent)
    )
    JENV.globals = {
            'jasons_kickstart_compiler' : jinja_globals,
            'Path' : Path
    }
    TEMPLATE : Final[Template] = JENV.get_template(INPUT_FILE_PATH.name)
    OUTPUT_PATH : Final[Path] = Path("ks.cfg")
    with OUTPUT_PATH.open('w') as output_file:
        output_file.write(TEMPLATE.render())
