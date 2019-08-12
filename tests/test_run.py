from subprocess import Popen
from time import sleep
# x = Popen("python client.py server --add 1", shell=True)
# x.wait()
# x = Popen("python client.py server --add 2", shell=True)
# x.wait()
# x = Popen("python client.py server --add 3", shell=True)
# x.wait()


x = Popen("python client.py simulation monkey_program.py --name test1 --cores 4 --arguments 20", shell=True)
x.wait()
x = Popen("python client.py simulation monkey_program.py --name test2 --cores 20 --arguments 60", shell=True)
x.wait()
x = Popen("python client.py simulation monkey_program.py --name test3 --cores 8 --arguments 15", shell=True)
x.wait()
x = Popen("python client.py simulation monkey_program.py --name test4 --cores 10 --arguments 25", shell=True)
x.wait()

x = Popen("python client.py status --report", shell=True)
x.wait()
sleep(6)
x = Popen("python client.py status --report", shell=True)
x.wait()