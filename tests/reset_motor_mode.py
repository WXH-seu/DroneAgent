import time
import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


URI = "radio://0/80/2M/E7E7E7E715"


def set_param(cf, name, value):
    try:
        cf.param.set_value(name, str(value))
        print(f"Set {name} = {value}")
        time.sleep(0.3)
    except Exception as e:
        print(f"Skip {name}: {e}")


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Connected.")

        set_param(cf, "motorPowerSet.m1", 0)
        set_param(cf, "motorPowerSet.m2", 0)
        set_param(cf, "motorPowerSet.m3", 0)
        set_param(cf, "motorPowerSet.m4", 0)
        set_param(cf, "motorPowerSet.enable", 0)

        for _ in range(20):
            cf.commander.send_stop_setpoint()
            time.sleep(0.05)

        print("Motor direct mode disabled and commander stopped.")


if __name__ == "__main__":
    main()
