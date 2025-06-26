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
                return None, None, None, None
        elif args[i] == '>>':
            if i + 1 < len(args):
                stdout_file = args[i + 1].strip('"\'')
                stdout_append = True
                i += 2
                continue
            else:
                print('Error: missing filename after >>')
                return None, None, None, None
        elif args[i] == '<':
            if i + 1 < len(args):
                stdin_file = args[i + 1].strip('"\'')
                i += 2
                continue
            else:
                print('Error: missing filename after <')
                return None, None, None, None
        else:
            filtered_args.append(args[i])
            i += 1
    return filtered_args, stdin_file, stdout_file, stdout_append

    
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
        cmd_args, stdin_file, stdout_file, stdout_append = parse_redirection(args)
        if cmd_args is None:
            continue
        
        # Setup redirection
        stdin = None
        stdout = None
        try:
            if stdin_file:
                stdin = open(stdin_file, 'r')
            if stdout_file:
                mode = 'a' if stdout_append else 'w'
                stdout = open(stdout_file, mode)
        except Exception as e:
            print(f"Redirection error: {e}")
            continue
        
        # Builtins
        if cmd in BUILTINS:
            if stdout:
                with redirect_stdout(stdout):
                    BUILTINS[cmd](*cmd_args)
            else:
                BUILTINS[cmd](*cmd_args)
        else:
            path = shutil.which(cmd)
            if path:
                try:
                    subprocess.run([cmd] + cmd_args, stdin=stdin, stdout=stdout or sys.stdout)
                except Exception as e:
                    print(f"Execution error: {e}")
            else:
                print(f"{cmd}: command not found")
        if stdin:
            stdin.close()
        if stdout:
            stdout.close()

if __name__ == "__main__":
    main()
