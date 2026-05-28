import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


URI = "radio://0/80/2M/E7E7E7E715"


def main():
    cflib.crtp.init_drivers()

    print(f"Connecting to {URI} ...")

    with SyncCrazyflie(URI) as scf:
        print("Connected.")

        print("Starting PositionHlCommander...")
        with PositionHlCommander(
            scf,
            default_height=1.0,
            default_velocity=0.5,
            controller=PositionHlCommander.CONTROLLER_PID,
        ) as pc:
            print("Takeoff to 0.3m.")
            time.sleep(2.0)

        print("Landed.")

    print("Disconnected.")


if __name__ == "__main__":
    main()
