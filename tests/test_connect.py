import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"

def main():
    cflib.crtp.init_drivers()

    print(f"Connecting to {URI} ...")

    try:
        with SyncCrazyflie(URI) as scf:
            print("Connected.")
            time.sleep(3)

        print("Disconnected.")

    except Exception as e:
        print("Connection failed.")
        print(repr(e))


if __name__ == "__main__":
    main()
