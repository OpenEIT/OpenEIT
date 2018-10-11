
# import matplotlib
# matplotlib.use("TkAgg")

import argparse
import logging
import OpenEIT.dashboard
import configparser
import Adafruit_BluefruitLE

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
# 
# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()

# TODO: Improve State Feedback
# The current connection and playback state should be clearly visible
# at all times
# Test all buttons and functions with the device and flag any problems. 
# Create a way to select the reconstruction algorithm. 
# 
def main():

    configParser = configparser.ConfigParser()   
    configFilePath = r'configuration.txt'
    configParser.read(configFilePath)

    n_el        = configParser.get('hardware-config', 'n_el')
    algorithm   = configParser.get('software-config', 'algorithm')
    mode        = configParser.get('software-config', 'mode')
    fwsequence  = configParser.get('software-config', 'fwsequence')    

    ap = argparse.ArgumentParser()

    ap.add_argument("-f", "--read-file",
                    action="store_true",
                    default=False)
    ap.add_argument("--virtual-tty",
                    action="store_true",
                    default=False)
    ap.add_argument("port", nargs="?")

    args = ap.parse_args()

    controller = OpenEIT.dashboard.Controller()
    
    controller.configure(
        initial_port=args.port,
        read_file=args.read_file,
        virtual_tty=args.virtual_tty,
        n_el= n_el,
        algorithm=algorithm,
        mode=mode,
        fwsequence=fwsequence
    )

    gui = OpenEIT.dashboard.runGui(controller)
    gui.run()


if __name__ == "__main__":

    main()
