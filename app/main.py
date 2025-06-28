import sys
import shutil # copy and archive dir trees
import subprocess
import os
from contextlib import ExitStack, redirect_stdout, redirect_stderr
import shlex
import glob
import readline
import atexit

HISTORY_FILE = os.path.expanduser("~/.your_shell_history")

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


def history_cmd(*args):
    """Enhanced history command with support for:
    - history: show all history
    - history n: show last n entries
    - history -c: clear history
    - history -w [file]: write current history to file
    - history -r [file]: read history from file
    """
    if not args:
        # Show all history
        for i in range(1, readline.get_current_history_length() + 1):
            item = readline.get_history_item(i)
            if item:
                print(f"    {i}  {item}")
    elif args[0] == "-c":
        # Clear history
        readline.clear_history()
        print("History cleared")
    elif args[0] == "-w":
        # Write history to file
        file_path = args[1] if len(args) > 1 else HISTORY_FILE
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            readline.write_history_file(file_path)
            print(f"History written to {file_path}")
        except (IOError, OSError) as e:
            print(f"Error writing history: {e}")
    elif args[0] == "-r":
        # Read history from file
        file_path = args[1] if len(args) > 1 else HISTORY_FILE
        try:
            if os.path.exists(file_path):
                readline.read_history_file(file_path)
                # Don't print success message to avoid interfering with prompt
            else:
                # Don't print error message to avoid interfering with prompt
                pass
        except (IOError, OSError):
            # Don't print error message to avoid interfering with prompt
            pass
    elif args[0].isdigit():
        # Show last n entries
        n = int(args[0])
        total = readline.get_current_history_length()
        start = max(1, total - n + 1)
        end = total + 1
        for i in range(start, end):
            item = readline.get_history_item(i)
            if item:
                print(f"    {i}  {item}")
    else:
        print("Usage: history [n] | history [-c|-w|-r] [file]")
        print("  n     : show last n history entries")
        print("  -c    : clear history")
        print("  -w    : write history to file")
        print("  -r    : read history from file")


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
    "cd"  : cdh,
    "history": history_cmd
}

def run_pipeline(line):
    commands = [cmd.strip() for cmd in line.split('|')]
    num_commands = len(commands)
    pids = []
    
    # Create pipes
    pipes = [os.pipe() for _ in range(num_commands - 1)]
    
    for i, command_str in enumerate(commands):
        pid = os.fork()
        if pid == 0: # Child process
            # Input redirection
            if i > 0:
                os.dup2(pipes[i-1][0], sys.stdin.fileno())

            # Output redirection
            if i < num_commands - 1:
                os.dup2(pipes[i][1], sys.stdout.fileno())

            # Close all pipe ends in the child
            for p_read, p_write in pipes:
                os.close(p_read)
                os.close(p_write)

            # Parse and execute command
            args = parse_args(command_str)
            cmd = args[0]
            cmd_args, stdin_f, stdout_f, stdout_app, stderr_f, stderr_app = parse_redirection(args[1:])
            
           
            # For simplicity, file redirections inside a pipe are ignored,
            # except for the first command's input and last command's output.

            try:
                if cmd in BUILTINS:
                    BUILTINS[cmd](*cmd_args)
                    os._exit(0) # Exit after builtin runs
                else:
                    os.execvp(cmd, [cmd] + cmd_args)
            except FileNotFoundError:
                print(f"{cmd}: command not found", file=sys.stderr)
                os._exit(1)
            except Exception as e:
                print(f"Error executing {cmd}: {e}", file=sys.stderr)
                os._exit(1)

        else: # Parent process
            pids.append(pid)

    # Close all pipe ends in the parent
    for p_read, p_write in pipes:
        os.close(p_read)
        os.close(p_write)

    # Wait for all children to complete
    for pid in pids:
        os.waitpid(pid, 0)
        
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
            try:
                subprocess.run(
                    [cmd, *args],
                    stdin=(f if stdin_f else None),
                    stdout=(out if stdout_f else None),
                    stderr=(err if stderr_f else None)
                )
            except FileNotFoundError:
                print(f"{cmd}: command not found")
            except Exception as e:
                print(f"{cmd}: command not found")

def get_all_commands():
    paths= os.environ.get("PATH", "").split(os.pathsep)
    cmds= set(BUILTINS)
    for path in paths:
        if os.path.isdir(path):
            try:
                for fname in os.listdir(path):
                    fpath = os.path.join(path, fname)
                    if os.access(fpath, os.X_OK) and not os.path.isdir(fpath):
                        cmds.add(fname)
            except (PermissionError, FileNotFoundError):
                continue
    return cmds

# A simplified completer that provides matches to readline,
# allowing readline's default behavior to handle common prefix completion.
class BashCompleter:
    def __init__(self, commands):
        self.commands = commands
        self.matches = []

    def __call__(self, text, state):
        line = readline.get_line_buffer()
        parts = line.split()
        if not parts or (len(parts) == 1 and not line.endswith(' ')):
            options = sorted([cmd for cmd in self.commands if cmd.startswith(text)])
            if state == 0:
                if not options:
                    return None
                common = os.path.commonprefix(options)
                # If the common prefix is a unique match, append a space
                if common and common != text:
                    if options.count(common) == 1 or (len(options) == 1 and options[0] == common):
                        return common + ' '
                    return common
                if len(options) == 1:
                    return options[0] + ' '
            if state < len(options):
                return options[state]
            return None
        else:
            options = sorted(glob.glob(text + '*'))
            if state == 0:
                if not options:
                    return None
                common = os.path.commonprefix(options)
                if common and common != text:
                    if options.count(common) == 1 or (len(options) == 1 and options[0] == common):
                        return common + ' '
                    return common
                if len(options) == 1:
                    return options[0] + ' '
            if state < len(options):
                return options[state]
            return None


def redisplay_prompt(prompt="$ "):
    sys.stdout.write('\r' + prompt + readline.get_line_buffer())
    sys.stdout.flush()

def completion_display_hook(substitution, matches, longest_match_length):
    line_buffer = readline.get_line_buffer()
    columns = os.environ.get("COLUMNS", 80)

    print()

    buffer = ""
    for match in matches:
        buffer += match + "  "
    print(buffer)

    redisplay_prompt()


def main():
    # Get all commands at startup
    all_commands = get_all_commands()
    
    # setup bash-like completion via the simplified BashCompleter
    completer = BashCompleter(all_commands)
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.set_completion_display_matches_hook(completion_display_hook)

    # Setup history
    try:
        # Load history on startup (both interactive and non-interactive)
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
            # Limit history file size to prevent it from growing too large
            readline.set_history_length(1000)
    except (IOError, OSError):
        pass
    
    # Register history save function for both interactive and non-interactive modes
    def save_history():
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            readline.write_history_file(HISTORY_FILE)
        except (IOError, OSError):
            pass
    
    atexit.register(save_history)

    # print("Shell started. Type 'exit' to quit.")
    
    while True:
        try:
            line = input("$ ")
            if not line.strip():
                continue

            # Add command to history (avoid duplicates and empty lines)
            if line.strip():
                # Check if this is different from the last history item
                should_add = True
                history_len = readline.get_current_history_length()
                
                if history_len > 0:
                    last_item = readline.get_history_item(history_len)
                    if last_item == line:
                        should_add = False
                
                if should_add:
                    readline.add_history(line)
                    
                    # Optional: Periodically save history during long sessions
                    # This ensures history is preserved even if shell crashes
                    new_len = readline.get_current_history_length()
                    if new_len % 50 == 0:  # Save every 50 commands
                        try:
                            readline.write_history_file(HISTORY_FILE)
                        except (IOError, OSError):
                            pass

            if '|' in line:
                run_pipeline(line)
                continue

            command = parse_args(line)
            if not command:
                continue

            cmd = command[0]
            args = command[1:]
            
            result = parse_redirection(args)
            if result is None:
                continue
            
            cmd_args, stdin_file, stdout_file, stdout_append, stderr_file, stderr_append = result
            
            run_cmd(cmd, cmd_args, stdin_file, stdout_file, stdout_append, stderr_file, stderr_append)

        except KeyboardInterrupt:
            print() 
            continue 
        except EOFError:
            print()  
            break


if __name__ == "__main__":
    main()
