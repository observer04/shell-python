from ast import arg
import builtins
import cmd
import sys
import shutil # copy and archive dir trees
import subprocess
import os
from contextlib import redirect_stdout, redirect_stderr

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

import shlex

def parse_args(line):
    try:
        return shlex.split(line)
    except ValueError as e:
        # Handle malformed quotes with more sophisticated parsing
        if "No closing quotation" in str(e):
            print(f"Warning: Malformed quotes detected. Using simple parsing.")
            return line.split()
        else:
            # Re-raise other shlex errors
            raise
 
def parse_redirection(args):
    """
    Parses args for redirection operators and returns:
    (filtered_args, stdin_file, stdout_file, stdout_append)
    Only the last redirection of each type is used.
    """
    stdin_file = None
    stdout_file = None
    stdout_append = False
    stderr_file = None
    stderr_append = False
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] in ('>', '1>'):
            if i + 1 < len(args):          
                stdout_file = args[i + 1].strip('"\'')
                stdout_append = False
                i += 2      # skip the redirect op and the stdout_file from filtered_args
                continue
            else:
                print('Error: missing filename after >')
                return None, None, None, None, None, None
        elif args[i] == '>>':
            if i + 1 < len(args):
                stdout_file = args[i + 1].strip('"\'')
                stdout_append = True
                i += 2
                continue
            else:
                print('Error: missing filename after >>')
                return None, None, None, None, None, None
        elif args[i] == '<':
            if i + 1 < len(args):
                stdin_file = args[i + 1].strip('"\'')
                i += 2
                continue
            else:
                print('Error: missing filename after <')
                return None, None, None, None, None, None
        elif args[i] == '2>':
            if i + 1 < len(args):
                stderr_file = args[i + 1].strip('"\'')
                stderr_append = False
                i += 2
                continue
            else:
                print('Error: missing filename after 2>')
                return None, None, None, None, None, None
        elif args[i] == '2>>':
            if i + 1 < len(args):
                stderr_file = args[i + 1].strip('"\'')
                stderr_append = True
                i += 2
                continue
            else:
                print('Error: missing filename after 2>>')
                return None, None, None, None, None, None
        else:
            filtered_args.append(args[i])
            i += 1
    return filtered_args, stdin_file, stdout_file, stdout_append, stderr_file, stderr_append

    
BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": type_cmd,
    "pwd" : lambda *_ : print(os.getcwd()),
    "cd"  : cdh
}
        
def main():
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
        stdin = None
        stdout = None
        stderr = None
        try:
            if stdin_file:
                stdin = open(stdin_file, 'r')
            if stdout_file:
                mode = 'a' if stdout_append else 'w'
                stdout = open(stdout_file, mode)
            if stderr_file:
                mode = 'a' if stderr_append else 'w'
                stderr = open(stderr_file, mode)
        except Exception as e:
            print(f"Redirection error: {e}")
            if stdin:
                stdin.close()
            if stdout:
                stdout.close()
            if stderr:
                stderr.close()
            continue
        # Builtins
        if cmd in BUILTINS:
            ctx_stdout = redirect_stdout(stdout) if stdout else None
            ctx_stderr = redirect_stderr(stderr) if stderr else None
            with ctx_stdout or dummy_context(), ctx_stderr or dummy_context():
                BUILTINS[cmd](*cmd_args)
        else:
            path = shutil.which(cmd)
            if path:
                try:
                    subprocess.run([cmd] + cmd_args, stdin=stdin, stdout=stdout or sys.stdout, stderr=stderr or sys.stderr)
                except Exception as e:
                    print(f"Execution error: {e}")
            else:
                print(f"{cmd}: command not found")
        if stdin:
            stdin.close()
        if stdout:
            stdout.close()
        if stderr:
            stderr.close()

# Add a dummy context manager for cases where no redirection is needed
from contextlib import contextmanager
def dummy_context():
    @contextmanager
    def _dummy():
        yield
    return _dummy()

if __name__ == "__main__":
    main()
