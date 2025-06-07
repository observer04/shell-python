import builtins
import cmd
import sys
import shutil # copy and archive dir trees

def type_cmd(cmd, *_):
    if cmd in BUILTINS:
        print(f"{cmd} is a shell builtin")
    elif path:=shutil.which(cmd):       #like os.environ.get("PATH")
        print(f"{cmd} is {path}")
    else:           
        print(f"{cmd}: not found")

BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": type_cmd,
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
            print(f"{cmd}: command not found")
        
        
        
if __name__ == "__main__":
    main()
