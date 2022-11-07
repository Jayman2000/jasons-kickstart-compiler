from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from base64 import standard_b64encode
from crypt import crypt
from getpass import getpass
from io import BytesIO
from pathlib import Path
from shlex import quote as shell_quote
from sys import stderr
from tarfile import TarInfo, open as open_tar
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Template
from typing_extensions import Final


ENTRY_POINT_MISSING : Final[str] = \
        "ERROR: A self extracting post script lacks a file named " \
        + "entry-point. The self extracting post script won’t " \
        + "do anything."
OWNER_EXECUTABLE_BIT : int = 0o0100


def get_field(
        name : str,
        prompt : Optional[str] = None,
        is_password : bool = False,
        encrypt_password : bool = True
) -> str:
    while True:
        if prompt is None:
            prompt = f"{name}: "
        if is_password:
            password : str = getpass(prompt)
            if password == getpass("Type that same password again: "):
                if encrypt_password:
                    password = crypt(password)
                return password
            else:
                print("Passwords don’t match. Try again.")
        else:
            return input(prompt)


def self_extracting_post_script(
        path : Path,
        input_file_parent : Path
) -> str:
    if not path.is_absolute():
        path = Path(input_file_parent, path)
    # It’s kind of weird to declare a function inside of another
    # function, but this is an easy way to give filter() access to
    # encountered_entry_point. I could make encountered_entry_point a
    # global variable, but it would still have to get reset every time
    # self_extracting_post_script() gets run. Plus, keeping it a local
    # variable theoretically allows you to run
    # to self_extracting_post_script() multiple times at once.
    encountered_entry_point : bool = False
    def filter(tar_info : TarInfo) -> TarInfo:
        if tar_info.name == "entry-point":
            nonlocal encountered_entry_point
            encountered_entry_point = True
            if tar_info.mode & OWNER_EXECUTABLE_BIT == 0:
                print(
                        "A self-extracting post script’s entry-point’s "
                        + "owner’s executable bit wasn’t set. "
                        + "Automatically setting it…"
                )
                tar_info.mode |= OWNER_EXECUTABLE_BIT
        return tar_info

    # Credit goes to decaf (https://stackoverflow.com/users/1159217/decaf)
    # for this idea: <https://stackoverflow.com/a/15858237/7593853>
    tar_data = BytesIO()
    with open_tar(fileobj=tar_data, mode='w') as tar:
        tar.add(
                path,
                arcname=Path("/", path.name),
                recursive=True,
                filter=filter
        )
    if encountered_entry_point:
        base_64_tar_data : str = standard_b64encode(tar_data.getvalue()).decode()
        if "%end" in base_64_tar_data:
            print(
                    "ERROR: encoded data contains “%end”. This should "
                    + "never happen. The resulting kickstart file won’t "
                    + "work.",
                    file=stderr
            )
        return f"""%post --interpreter=/usr/bin/bash --log=/root/jasons-kickstart-compiler_self-extracting-post.log
declare -r temporary_directory="$(mktemp -d)"
cd "$temporary_directory"
echo -n {shell_quote(base_64_tar_data)} | base64 -d | tar -x
./entry-point
cd /
rm -rf "$temporary_directory"
%end
"""
    else:
        ERROR_MESSAGE : Final[str] = "ERROR: didn’t find a file name " \
                + f"“entry-point” in {str(path)}. Can’t generate a " \
                + "self-extracting post script."
        print(ERROR_MESSAGE, file=stderr)
        return f"# {ERROR_MESSAGE}"


def main():
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

    JENV : Final[Environment] = Environment(
            loader=FileSystemLoader(INPUT_FILE_PATH.parent)
    )
    JENV.globals = {
            'get_field' : get_field,
            'input_file_parent' : INPUT_FILE_PATH.parent,
            'Path' : Path,
            'self_extracting_post_script' : self_extracting_post_script
    }
    TEMPLATE : Final[Template] = JENV.get_template(INPUT_FILE_PATH.name)
    OUTPUT_PATH : Final[Path] = Path("ks.cfg")
    with OUTPUT_PATH.open('w') as output_file:
        output_file.write(TEMPLATE.render())
