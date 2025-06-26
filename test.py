from contextlib import redirect_stdout
import io, sys

buf = io.StringIO()
print("before")
with redirect_stdout(buf):
    print("inside!")       # goes into buf, not the terminal
print("after")
print("buffered:", buf.getvalue())