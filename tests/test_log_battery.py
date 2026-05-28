import time

import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig


URI = "radio://0/80/2M/E7E7E7E715"


def log_callback(timestamp, data, logconf):
    print(
        f"t={timestamp} "
        f"vbat={data.get('pm.vbat')} "
        f"state={data.get('pm.state')}"
    )


def main():
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI) as scf:
        cf = scf.cf
        print("Connected.")

        logconf = LogConfig(name="Battery", period_in_ms=500)
        logconf.add_variable("pm.vbat", "float")
        logconf.add_variable("pm.state", "uint8_t")

        cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_callback)
        logconf.start()

        time.sleep(5)

        logconf.stop()

    print("Disconnected.")


if __name__ == "__main__":
    main()
