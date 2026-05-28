import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def send_for(cf, roll, pitch, yawrate, thrust, duration_s):
    end = time.time() + duration_s
    while time.time() < end:
        cf.commander.send_setpoint(roll, pitch, yawrate, thrust)
        time.sleep(0.02)


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Connected.")
        time.sleep(1.0)

        print("Arming low thrust stream.")
        send_for(cf, 0.0, 0.0, 0.0, 10001, 1.0)

        print("Attempting very short lift.")
        # Brushless 需要的 thrust 可能不同。
        # 从 18000 开始，不够再逐步加，不要一次加太大。
        send_for(cf, 0.0, 0.0, 0.0, 18000, 1.0)

        print("Descending.")
        send_for(cf, 0.0, 0.0, 0.0, 12000, 0.5)

        print("Stopping.")
        for _ in range(30):
            cf.commander.send_stop_setpoint()
            time.sleep(0.02)

    print("Disconnected.")


if __name__ == "__main__":
    main()

