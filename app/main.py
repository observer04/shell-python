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
            path = os.path.expanduser("~")
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")

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
        command= input().split()
        #separate cmd and args
        cmd = command[0]
        args= command[1:] # a list of rest strings
        #check cmd
        if cmd in BUILTINS:
            BUILTINS[cmd](*args)    # ["Hello", "World"], *args becomes "Hello", "World"
        else :
            path = shutil.which(cmd)        #doesnt need full path so just check if cmd exists in path
            if path:
                subprocess.run([cmd] + args)
            else :
                print(f"{cmd}: command not found")
            
        
        
if __name__ == "__main__":
    main()
