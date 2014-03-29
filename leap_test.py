import communication as com
from controllers import *

def main():
    set_current_controller([PotteryListener, GrabListener])

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()

    # Remove the sample listener when done
    disable_current_controller()

if __name__ == '__main__':
    com.dont_use_network = True
    main()
