import builtins
import cmd
import sys

BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": lambda cmd, *_: print(f"{cmd} is a shell builtin") if cmd in BUILTINS 
    else print(f"{cmd} not found")
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
