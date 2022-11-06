from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
import typing

# typing.Final was added in Python 3.8 [1], but Python 3.7 is still
# supported [2]. I want this program to work on all currently supported
# version of Python (RHEL users are likely a few versions behind).
#
# Luckily, Union[x] == x, so we can use Union when Final isn’t
# available.
#
# Unfortunately, mypy running on Python 3.7 doesn’t like the following
# code:
#
#   if version_info.major <= 3 and version_info.minor <= 7:
#       from typing import Union as Final
#   else:
#       from typing import Final
#
# Mypy running on Python 3.7 complains that typing.Final doesn’t exist.
# I tried using a try…except ImportError, but mypy running on Python 3.7
# didn’t like that either. My work around is to use
# typing.__dict__.get().
#
# Unfortunately, mypy doesn’t like
# typing.__dict__.get("Final", default=typing.Union). That’s probably a
# bug with mypy, but I can use an if statement to work around it easily.
#
# [1]: <https://docs.python.org/3/library/typing.html?highlight=3.8#typing.Final>
# [2]: <https://web.archive.org/web/20221106151109/https://devguide.python.org/versions/#supported-versions>
Final = typing.__dict__.get("Final")
if Final is None:
    Final = typing.Union


def main():
    DESCRIPTION : Final[str] = \
            "Turn a set of files into a standalone ks.cfg. " \
            + "<https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/performing_an_advanced_rhel_9_installation/installation-methods-advanced_installing-rhel-as-an-experienced-user>"
    FILE_HELP : final = \
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
