import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def set_param_if_exists(cf, name, value):
    try:
        cf.param.set_value(name, value)
        print(f"Set {name} = {value}")
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"Skip {name}: {e}")
        return False


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Connected.")

        # 不同固件版本参数名可能不同，能设置哪个用哪个
        set_param_if_exists(cf, "system.arm", "1")
        set_param_if_exists(cf, "motorPowerSet.enable", "1")

        print("Sending low thrust setpoints. REMOVE PROPS.")
        for _ in range(100):
            cf.commander.send_setpoint(0.0, 0.0, 0.0, 15000)
            time.sleep(0.02)

        print("Stopping.")
        for _ in range(20):
            cf.commander.send_stop_setpoint()
            time.sleep(0.05)

        set_param_if_exists(cf, "system.arm", "0")
        set_param_if_exists(cf, "motorPowerSet.enable", "0")

    print("Disconnected.")


if __name__ == "__main__":
    main()
