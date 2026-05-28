import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


URI = "radio://0/80/2M/E7E7E7E715"

# 第一次建议设成 0.5；确认稳定后再改成 1.0。
SCALE = 0.5

WAYPOINTS = [
    (0.0, 0.0, 1.0 * SCALE),
    (0.0, 1.0 * SCALE, 1.0 * SCALE),
    (1.0 * SCALE, 1.0 * SCALE, 1.0 * SCALE),
    (1.0 * SCALE, 0.0, 1.0 * SCALE),
    (0.0, 0.0, 1.0 * SCALE),
]


deck_attached_event = Event()
position = {"x": 0.0, "y": 0.0, "z": 0.0}


def deck_flow_callback(_, value_str):
    value = int(value_str)
    print(f"deck.bcFlow2 = {value}")

    if value:
        deck_attached_event.set()
        print("Flow deck detected.")
    else:
        print("Flow deck NOT detected.")


def position_callback(timestamp, data, logconf):
    position["x"] = data["stateEstimate.x"]
    position["y"] = data["stateEstimate.y"]
    position["z"] = data["stateEstimate.z"]

    print(
        f"pos x={position['x']:.2f}, "
        f"y={position['y']:.2f}, "
        f"z={position['z']:.2f}"
    )


def reset_estimator(cf):
    print("Resetting Kalman estimator...")

    cf.param.set_value("kalman.resetEstimation", "1")
    time.sleep(0.2)
    cf.param.set_value("kalman.resetEstimation", "0")

    # 等估计器重新稳定
    time.sleep(2.0)

    print("Estimator reset done.")


def setup_position_log(cf):
    logconf = LogConfig(name="Position", period_in_ms=200)
    logconf.add_variable("stateEstimate.x", "float")
    logconf.add_variable("stateEstimate.y", "float")
    logconf.add_variable("stateEstimate.z", "float")

    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(position_callback)

    return logconf


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

        time.sleep(1.0)

        if not deck_attached_event.wait(timeout=5):
            print("No Flow deck detected. Abort.")
            return

        reset_estimator(cf)

        logconf = setup_position_log(cf)
        logconf.start()

        print("Arming...")
        cf.supervisor.send_arming_request(True)
        time.sleep(1.0)

        print("Starting square waypoint flight.")

        try:
            with PositionHlCommander(
                scf,
                x=0.0,
                y=0.0,
                z=0.0,
                default_velocity=0.25,
                default_height=1.0 * SCALE,
                controller=PositionHlCommander.CONTROLLER_PID,
            ) as pc:
                # 进入上下文后会自动起飞到 default_height
                time.sleep(2.0)

                for x, y, z in WAYPOINTS:
                    print(f"Going to x={x:.2f}, y={y:.2f}, z={z:.2f}")
                    pc.go_to(x, y, z)
                    time.sleep(2.5)

                print("Returning to origin and landing.")
                pc.go_to(0.0, 0.0, 1.0 * SCALE)
                time.sleep(2.0)

            print("Landed.")

        finally:
            print("Stopping position log.")
            logconf.stop()

            print("Sending stop setpoint.")
            for _ in range(20):
                cf.commander.send_stop_setpoint()
                time.sleep(0.05)

    print("Disconnected.")


if __name__ == "__main__":
    main()
