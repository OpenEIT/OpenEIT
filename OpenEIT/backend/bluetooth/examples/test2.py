import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART
import uuid

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()
# RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
# Main function implements the program logic so it can run in a background
# thread.  Most platforms require the main thread to handle GUI events and other
# asyncronous events like BLE actions.  All of the threading logic is taken care
# of automatically though and you just need to provide a main function that uses
# the BLE provider.
def m():
    # Clear any cached data because both bluez and CoreBluetooth have issues with
    # caching data and it going stale.
    ble.clear_cached_data()

    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    adapter.power_on()
    print('Using adapter: {0}'.format(adapter.name))

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print('Disconnecting any connected UART devices...')
    UART.disconnect_devices()

    # Scan for UART devices.
    print('Searching for UART device...')
    try:
        adapter.start_scan()
        # Search for the first UART device found (will time out after 60 seconds
        # but you can specify an optional timeout_sec parameter to change it).
        device = UART.find_device()
        if device is None:
            raise RuntimeError('Failed to find UART device!')
    finally:
        # Make sure scanning is stopped before exiting.
        adapter.stop_scan()



    print('Connecting to device...')
    device.connect()  # Will time out after 60 seconds, specify timeout_sec parameter
                      # to change the timeout.

    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    try:
        # Wait for service discovery to complete for the UART service.  Will
        # time out after 60 seconds (specify timeout_sec parameter to override).
        print('Discovering services...')
        UART.discover(device)

        # Once service discovery is complete create an instance of the service
        # and start interacting with it.
        uart = UART(device)
        # dis = DeviceInformation(device)
        # Write a string to the TX characteristic.
        # uart.write('Hello world!\r\n')
        # print("Sent 'Hello world!' to the device.")
        # print('Subscribing to RX characteristic changes...')
        # data = []
        # print(uart._rx_received(data))
        def received(data):
            print('Received: {0}',data)

        # rx = uart.find_characteristic(RX_CHAR_UUID)
        # Turn on notification of RX characteristics using the callback above.
        # print('Subscribing to RX characteristic changes...')
        # rx.start_notify(received)
        print(dir(device))
        while (device._connected):
            # Now wait up to one minute to receive data from the device.
            # print('Waiting up to 60 seconds to receive data from the device...')
            received = uart.read(timeout_sec=60)

            if received is not None:
                # print (len(received))
                # for i in range(received):
                #     print (received[i])
                # Received data, print it out.
                print('Received: {0}'.format(received))
            else:
                # Timeout waiting for data, None is returned.
                print('Received no data!')


    finally:
        print('this is where disconnect should go')
        # dis = DeviceInformation(device)
        # Make sure device is disconnected on exit.
        device.disconnect()


def main():
    # Initialize the BLE system.  MUST be called before other BLE calls!
    ble.initialize()
    # Start the mainloop to process BLE events, and run the provided function in
    # a background thread.  When the provided main function stops running, returns
    # an integer status code, or throws an error the program will exit.
    ble.run_mainloop_with(m)

if __name__ == "__main__":

    main()