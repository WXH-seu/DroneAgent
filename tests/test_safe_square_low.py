import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


URI = "radio://0/80/2M/E7E7E7E715"

HEIGHT = 0.25
SIZE = 0.20
VELOCITY = 0.10
HOLD_TIME = 1.5

deck_attached_event = Event()
pos = {"x": 0.0, "y": 0.0, "z": 0.0}


def deck_flow_callback(_, value_str):
    if int(value_str):
        deck_attached_event.set()
        print("Flow deck detected.")


def pos_callback(timestamp, data, logconf):
    pos["x"] = data["stateEstimate.x"]
    pos["y"] = data["stateEstimate.y"]
    pos["z"] = data["stateEstimate.z"]
    print(f"x={pos['x']:.2f}, y={pos['y']:.2f}, z={pos['z']:.2f}")


def reset_estimator(cf):
    print("Reset estimator.")
    cf.param.set_value("kalman.resetEstimation", "1")
    time.sleep(0.2)
    cf.param.set_value("kalman.resetEstimation", "0")
    time.sleep(3.0)


def emergency_stop(cf):
    print("Emergency stop.")
    for _ in range(50):
        cf.commander.send_stop_setpoint()
        time.sleep(0.02)


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        cf = scf.cf
        print("Connected.")

        cf.param.add_update_callback(
            group="deck",
            name="bcFlow2",
            cb=deck_flow_callback,
        )

        if not deck_attached_event.wait(timeout=5):
            print("No Flow deck detected. Abort.")
            return

        reset_estimator(cf)

        logconf = LogConfig(name="Position", period_in_ms=200)
        logconf.add_variable("stateEstimate.x", "float")
        logconf.add_variable("stateEstimate.y", "float")
        logconf.add_variable("stateEstimate.z", "float")
        cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(pos_callback)
        logconf.start()

        try:
            print("Arm.")
            cf.supervisor.send_arming_request(True)
            time.sleep(1.0)

            waypoints = [
                (0.0, 0.0, HEIGHT),
                (0.0, SIZE, HEIGHT),
                (SIZE, SIZE, HEIGHT),
                (SIZE, 0.0, HEIGHT),
                (0.0, 0.0, HEIGHT),
            ]

            with PositionHlCommander(
                scf,
                x=0.0,
                y=0.0,
                z=0.0,
                default_height=HEIGHT,
                default_velocity=VELOCITY,
                controller=PositionHlCommander.CONTROLLER_PID,
            ) as pc:
                time.sleep(2.0)

                for x, y, z in waypoints:
                    if pos["z"] > 0.60:
                        print("Height too high. Abort.")
                        break

                    print(f"go_to x={x:.2f}, y={y:.2f}, z={z:.2f}")
                    pc.go_to(x, y, z)
                    time.sleep(HOLD_TIME)

            print("Landed.")

        finally:
            logconf.stop()
            emergency_stop(cf)

    print("Disconnected.")


if __name__ == "__main__":
    main()
