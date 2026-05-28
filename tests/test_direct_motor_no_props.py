import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def set_param(cf, name, value):
    try:
        cf.param.set_value(name, str(value))
        print(f"Set {name} = {value}")
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"Failed {name}: {e}")
        return False


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Connected.")
        time.sleep(1.0)

        print("ENABLE direct motor power. REMOVE PROPS.")
        set_param(cf, "motorPowerSet.enable", 1)

        # 先全部置零
        for m in ["m1", "m2", "m3", "m4"]:
            set_param(cf, f"motorPowerSet.{m}", 0)

        time.sleep(0.5)

        # 逐个电机低功率测试
        # 如果完全不转，可以把 8000 改到 12000，再试一次。
        power = 12000

        for m in ["m1", "m2", "m3", "m4"]:
            print(f"Testing {m} at power {power}")
            set_param(cf, f"motorPowerSet.{m}", power)
            time.sleep(1.0)
            set_param(cf, f"motorPowerSet.{m}", 0)
            time.sleep(0.5)

        print("Disable direct motor power.")
        set_param(cf, "motorPowerSet.enable", 0)

    print("Disconnected.")


if __name__ == "__main__":
    main()
