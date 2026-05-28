import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Sending stop setpoints...")

        for _ in range(20):
            cf.commander.send_stop_setpoint()
            time.sleep(0.05)

        print("Emergency stop sent.")


if __name__ == "__main__":
    main()
