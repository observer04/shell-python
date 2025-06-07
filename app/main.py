import sys


def main():
    while True:
        # Uncomment this block to pass the first stage
        sys.stdout.write("$ ")
        sys.stdout.flush() 
        # Wait for user input
        command= input()
        com_and_args= command.split(" ")
        if com_and_args[0] == "exit":
            sys.exit(0)
        elif com_and_args[0] == "echo":
            print(" ".join(com_and_args[1:]))
        else:
            print(f"{command}: command not found")
    


if __name__ == "__main__":
    main()
