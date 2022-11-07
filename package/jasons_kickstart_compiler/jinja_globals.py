from base64 import standard_b64encode
from crypt import crypt
from getpass import getpass
from io import BytesIO
from pathlib import Path
from shlex import quote as shell_quote
from sys import stderr
from tarfile import TarInfo, open as open_tar
from typing import Optional

from typing_extensions import Final


ENTRY_POINT_MISSING : Final[str] = \
        "ERROR: A self extracting post script lacks a file named " \
        + "entry-point. The self extracting post script won’t " \
        + "do anything."
OWNER_EXECUTABLE_BIT : int = 0o0100
dependencies_for_self_extracting_post_script_called : bool = False
self_extracting_post_script_called : bool = False
input_file_parent : Path = Path()


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


def dependencies_for_self_extracting_post_script() -> str:
    global dependencies_for_self_extracting_post_script_called
    dependencies_for_self_extracting_post_script_called = True
    return """
bash
coreutils
tar
"""


def self_extracting_post_script(path : Path) -> str:
    global self_extracting_post_script_called
    self_extracting_post_script_called = True
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
