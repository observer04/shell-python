import builtins
import cmd
import sys
import shutil # copy and archive dir trees
import subprocess
import os

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
"""
import shlex

def parse_args(line):
    return shlex.split(line)
 
"""
        
def parse_args(line):
    args = []
    cur = ''
    in_single_quote = False
    i = 0
    while i< len(line):
        c=line[i]
        if c == "'" and not in_single_quote:
            in_single_quote = True
            i +=1
            continue
        elif c == "'" and in_single_quote:
            in_single_quote = False
            i +=1
            continue
        if in_single_quote:
            cur += c
        elif c.isspace():         #if next char outside '' is space cur is a one word arg.
            if cur !='':
                args.append(cur)
                cur = ''
        else:                   #echo ' osme  s' test 's d' first echo
            cur +=c
        i+=1
    if cur != '':
        args.append(cur)
    return args
    
BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": type_cmd,
    "pwd" : lambda *_ : print(os.getcwd()),
    "cd"  : cdh
}
        
def main():
    while True:
        # Uncomment this block to pass the first stage
        sys.stdout.write("$ ")
        sys.stdout.flush() 
        # Wait for user input
        command= parse_args(input())
        #separate cmd and args
        cmd = command[0]
        args= command[1:] # a list of rest strings
        #check cmd
        if cmd in BUILTINS:
            BUILTINS[cmd](*args)    # *> unpack =["Hello", "World"], *args becomes "Hello", "World"
        else :
            path = shutil.which(cmd)        #doesnt need full path so just check if cmd exists in path
            if path:
                subprocess.run([cmd] + args)
            else :
                print(f"{cmd}: command not found")
            
        
        
if __name__ == "__main__":
    main()
