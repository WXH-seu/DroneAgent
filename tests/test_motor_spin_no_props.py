import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Connected.")

        print("Sending low thrust setpoints. REMOVE PROPS.")
        for _ in range(80):
            # roll, pitch, yawrate, thrust
            # thrust 10001 很低，只用于看电机是否有反应；如无反应可试 15000
            cf.commander.send_setpoint(0.0, 0.0, 0.0, 15000)
            time.sleep(0.02)

        print("Stopping.")
        for _ in range(20):
            cf.commander.send_stop_setpoint()
            time.sleep(0.05)

    print("Disconnected.")


if __name__ == "__main__":
    main()
