import logging
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander


URI = "radio://0/80/2M/E7E7E7E715"
DEFAULT_HEIGHT = 0.1

deck_attached_event = Event()

logging.basicConfig(level=logging.ERROR)


def param_deck_flow(_, value_str):
    value = int(value_str)
    print("deck.bcFlow2 =", value)
    if value:
        deck_attached_event.set()
        print("Flow deck detected.")
    else:
        print("Flow deck NOT detected.")


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        cf = scf.cf
        print("Connected.")

        cf.param.add_update_callback(
            group="deck",
            name="bcFlow2",
            cb=param_deck_flow,
        )

        time.sleep(1.0)

        if not deck_attached_event.wait(timeout=5):
            print("No Flow deck detected. Abort.")
            return

        print("Arming...")
        cf.supervisor.send_arming_request(True)
        time.sleep(1.0)

        print("Taking off with MotionCommander.")
        with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
            print(f"Hovering at about {DEFAULT_HEIGHT} m for 5 seconds.")
            time.sleep(5.0)

        print("Landed.")

    print("Disconnected.")


if __name__ == "__main__":
    main()
