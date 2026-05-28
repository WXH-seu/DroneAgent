import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def main():
    cflib.crtp.init_drivers()

    print(f"Connecting to {URI} ...")

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf

        print("Connected.")
        time.sleep(1)

        params = [
            "radio.channel",
            "radio.address",
            "radio.bandwidth",
            "stabilizer.estimator",
            "stabilizer.controller",
        ]

        for name in params:
            try:
                value = cf.param.get_value(name)
                print(f"{name} = {value}")
            except Exception as e:
                print(f"{name}: failed: {e}")

        time.sleep(1)

    print("Disconnected.")


if __name__ == "__main__":
    main()
