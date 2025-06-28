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

# Wrap all history logic in a class
class HistoryManager:
    def __init__(self, file_path):
        self.file = file_path
        self.session_start = 0
        self.last_append_pos = 0
    def load(self):
        try:
            if sys.stdin.isatty() and os.path.exists(self.file):
                readline.read_history_file(self.file)
                self.session_start = readline.get_current_history_length()
                self.last_append_pos = self.session_start
                readline.set_history_length(1000)
        except:
            pass
    def save(self):
        try:
            if sys.stdin.isatty():
                d = os.path.dirname(self.file)
                if d: os.makedirs(d, exist_ok=True)
                readline.write_history_file(self.file)
        except:
            pass
    def add(self, line):
        if not line.strip(): return
        n = readline.get_current_history_length()
        last = readline.get_history_item(n) if n>0 else None
        if last != line:
            readline.add_history(line)
    def history_cmd(self, *args):
        if not args:
            start, end = 1, readline.get_current_history_length()+1
        elif args[0].isdigit():
            n=int(args[0]); tot=readline.get_current_history_length(); start=max(1, tot-n+1); end=tot+1
        elif args[0] in ('-c','-w','-a','-r'):
            mode=args[0]; f=args[1] if len(args)>1 else self.file
            try:
                d=os.path.dirname(f);
                if mode=='-c': readline.clear_history(); print("History cleared"); return
                if d: os.makedirs(d, exist_ok=True)
                if mode=='-w': readline.write_history_file(f); return
                if mode=='-r' and os.path.exists(f): readline.read_history_file(f); return
                if mode=='-a':
                    tot=readline.get_current_history_length()
                    with open(f,'a') as fh:
                        for i in range(self.last_append_pos+1, tot+1): item=readline.get_history_item(i); fh.write(item+'\n')
                    self.last_append_pos = tot
                    return
            except:
                return
        else:
            print("Usage: history [n] | history [-c|-w|-r|-a] [file]"); return
        for i in range(start,end):
            it=readline.get_history_item(i)
            if it: print(f"    {i}  {it}")

# Instantiate manager
history_mgr = HistoryManager(HISTORY_FILE)

# ...existing code...
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
    "cd"  : cdh,
    "history": history_mgr.history_cmd
}

def run_pipeline(line):
    commands = [cmd.strip() for cmd in line.split('|')]
    num_commands = len(commands)
    pids = []
    
    # Validate commands
    if num_commands < 2:
        return
    
    # Create pipes
    pipes = [os.pipe() for _ in range(num_commands - 1)]
    
    for i, command_str in enumerate(commands):
        pid = os.fork()
        if pid == 0: # Child process
            try:
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
                if not args:
                    os._exit(1)
                    
                cmd = args[0]
                cmd_args, stdin_f, stdout_f, stdout_app, stderr_f, stderr_app = parse_redirection(args[1:])
                
                # Handle file redirections for first and last commands only
                if i == 0 and stdin_f:
                    try:
                        fd = os.open(stdin_f, os.O_RDONLY)
                        os.dup2(fd, sys.stdin.fileno())
                        os.close(fd)
                    except OSError:
                        pass
                        
                if i == num_commands - 1 and stdout_f:
                    try:
                        flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if stdout_app else os.O_TRUNC)
                        fd = os.open(stdout_f, flags, 0o644)
                        os.dup2(fd, sys.stdout.fileno())
                        os.close(fd)
                    except OSError:
                        pass

                # Execute command
                if cmd in BUILTINS:
                    BUILTINS[cmd](*cmd_args)
                    os._exit(0)
                else:
                    os.execvp(cmd, [cmd] + cmd_args)
                    
            except FileNotFoundError:
                print(f"{cmd}: command not found", file=sys.stderr)
                os._exit(127)
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
        try:
            os.waitpid(pid, 0)
        except OSError:
            pass
        
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
                result = subprocess.run(
                    [cmd, *args],
                    stdin=(f if stdin_f else None),
                    stdout=(out if stdout_f else None),
                    stderr=(err if stderr_f else None),
                    check=False
                )
            except FileNotFoundError:
                print(f"{cmd}: command not found")
            except Exception:
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
    # Load history and register save on exit
    history_mgr.load()
    atexit.register(history_mgr.save)

    # Setup bash-like completion via the simplified BashCompleter
    completer = BashCompleter(get_all_commands())
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.set_completion_display_matches_hook(completion_display_hook)
    
    while True:
        try:
            line = input("$ ")
            if not line.strip():
                continue

            # Record command in history
            history_mgr.add(line)

            if '|' in line:
                run_pipeline(line)
                continue

            command = parse_args(line)
            if not command:
                continue

            cmd, *args = command
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
    # Initialize history manager
    history_mgr = HistoryManager(HISTORY_FILE)

    main()
