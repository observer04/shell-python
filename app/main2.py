import sys
import re
import logging
import os
import os.path

import subprocess


# logging.basicConfig(level=logging.INFO)

log = logging.getLogger("main")


def _exit(args):
    exit_code = int(args.split()[0])
    sys.exit(exit_code)


def _echo(args):
    print(args)


def _type(args):
    cmd = args.split()[0]
    if cmd in builtins:
        print(f"{cmd} is a shell builtin")
        return
    from_path = _get_from_path(cmd)
    if from_path:
        print(f"{cmd} is {from_path}")
        return
    print(f"{cmd}: not found")


def _get_from_path(cmd):
    paths = os.environ["PATH"].split(":")
    for path in paths:
        filename = f"{path}/{cmd}"
        if os.path.exists(filename):
            return filename
    return None


def _exec(cmd, args):
    os.system(f"{cmd} {args}")
    return


builtins = {
    "exit": _exit,
    "echo": _echo,
    "type": _type,
}


def main():

    # Wait for user input
    while True:
        sys.stdout.write("$ ")
        command = input()
        words = command.split()
        cmd = words[0]
        log.info("cmd was: %s" % (cmd))
        args = re.sub(re.compile(rf"{cmd}\s+"), "", command)
        if cmd in builtins:
            builtins[cmd](args)
            continue
        from_path = _get_from_path(cmd)
        if from_path:
            _exec(cmd, args)
            continue
        print(f"{command}: command not found")


if __name__ == "__main__":
    main()