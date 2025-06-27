import sys
import shutil # copy and archive dir trees
import subprocess
import os
from contextlib import ExitStack, redirect_stdout, redirect_stderr
import shlex
import glob
import readline
def type_cmd(cmd, *_):
    if cmd in BUILTINS:
        print(f"{cmd} is a shell builtin")
    elif path:=shutil.which(cmd):       #like os.environ.get("PATH")
        print(f"{cmd} is {path}")
    else:           
        print(f"{cmd}: not found")
        
def cdh(path=None, *_):
    try:
        if path is None:
            path = "~"
        path = os.path.expanduser(path)
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")



def parse_args(line):
    try:
        return shlex.split(line)
    except ValueError as e:
        if "No closing quotation" in str(e):
            return line.split()
        else:
            raise
 
def parse_redirection(args):
    ops = {
        '>':   ('stdout_file', False),
        '1>':  ('stdout_file', False),
        '1>>': ('stdout_file', True),
        '>>':  ('stdout_file', True),
        '<':   ('stdin_file',  False),
        '2>':  ('stderr_file', False),
        '2>>': ('stderr_file', True),
    }
    std = {
        'stdin_file': None,
        'stdout_file': None, 'stdout_append': False,
        'stderr_file': None, 'stderr_append': False
    }
    filtered = []
    i = 0
    while i < len(args):
        tok = args[i]
        if tok in ops:
            field, is_append = ops[tok]
            if i+1 >= len(args):
                print(f"Error: missing filename after {tok}")
                return None, *(None,)*5
            name = args[i+1].strip('"\'')
            std[field] = name
            if field == 'stdout_file' and is_append: std['stdout_append'] = True
            if field == 'stderr_file' and is_append: std['stderr_append'] = True
            i += 2
        else:
            filtered.append(tok)
            i += 1
    return filtered, std['stdin_file'], std['stdout_file'], std['stdout_append'], std['stderr_file'], std['stderr_append']

    
BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": type_cmd,
    "pwd" : lambda *_ : print(os.getcwd()),
    "cd"  : cdh
}
        
def run_cmd(cmd, args, stdin_f, stdout_f, stdout_app, stderr_f, stderr_app):
    with ExitStack() as stack:
        # 1) stdin
        if stdin_f:
            f = open(stdin_f, 'r')
            stack.enter_context(f)
            stack.enter_context(lambda: None)  # dummy to ensure close
        
        # 2) stdout
        if stdout_f:
            out = open(stdout_f, 'a' if stdout_app else 'w')
            stack.enter_context(out)
            stack.enter_context(redirect_stdout(out))
        
        # 3) stderr
        if stderr_f:
            err = open(stderr_f, 'a' if stderr_app else 'w')
            stack.enter_context(err)
            stack.enter_context(redirect_stderr(err))

        # 4) Execute
        if cmd in BUILTINS:
            BUILTINS[cmd](*args)
        else:
            subprocess.run(
                [cmd, *args],
                stdin=(f if stdin_f else None),
                stdout=(out if stdout_f else None),
                stderr=(err if stderr_f else None)
            )

def get_all_commands():
    paths= os.environ.get("PATH", "").split(os.pathsep)
    cmds= set(BUILTINS)
    for path in paths:
        if os.path.isdir(path):
            for fname in os.listdir(path):
                fpath = os.path.join(path, fname)
                if os.access(fpath, os.X_OK) and not os.path.isdir(fpath):
                    cmds.add(fname)
    return cmds
    
ALL_COMMANDS = get_all_commands()

# Encapsulated completer with bash-like double-TAB behavior
class BashCompleter:
    def __init__(self, commands):
        self.commands = commands
        self.last_prefix = None
        self.tab_count = 0

    def reset(self):
        self.last_prefix = None
        self.tab_count = 0

    def __call__(self, text, state):
        line = readline.get_line_buffer()
        parts = line.split()
        # Completing commands at start of line
        if len(parts) == 0 or (len(parts) == 1 and not line.endswith(' ')):
            options = [cmd for cmd in self.commands if cmd.startswith(text)]
            prefix = text
            if len(options) > 1:
                # multiple matches: bell or list
                if self.last_prefix == prefix and self.tab_count == 1:
                    print('\n' + '  '.join(options))
                    sys.stdout.write("$ ")
                    sys.stdout.flush()
                    self.reset()
                else:
                    print('\a', end='', flush=True)
                    self.last_prefix = prefix
                    self.tab_count = 1
                return None
            else:
                # single or no match: reset and return candidate
                self.reset()
                try:
                    return (options[state] + ' ') if state < len(options) else None
                except Exception:
                    return None
        # Completing filenames after command
        options = glob.glob(text + '*')
        self.reset()
        try:
            return (options[state] + ' ') if state < len(options) else None
        except Exception:
            return None


def main():
    # setup bash-like completion via BashCompleter
    completer = BashCompleter(ALL_COMMANDS)
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.set_pre_input_hook(completer.reset)
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            command = parse_args(input())
        except EOFError:
            break
        if not command:
            continue
        cmd = command[0]
        args = command[1:]
        # Parse redirections
        result = parse_redirection(args)
        if result is None:
            continue
        cmd_args, stdin_file, stdout_file, stdout_append, stderr_file, stderr_append = result
        try:
            run_cmd(cmd, cmd_args, stdin_file, stdout_file, stdout_append, stderr_file, stderr_append)
        except Exception as e:
            print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()
