import sys
from time import sleep

sleep_time = float(sys.argv[-1])
print("monkey {} starting".format(sleep_time))
sleep(sleep_time)




