import sys
from time import sleep

print("monkey input", sys.argv[-1])
sleep_time = float(sys.argv[-1])
print("monkey {} starting".format(sleep_time))
sleep(sleep_time)




