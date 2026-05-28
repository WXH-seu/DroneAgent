import time
from threading import Event
from typing import Dict, List, Tuple

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


class FlightSafetyError(RuntimeError):
    pass


class CrazyflieAdapter:
    def __init__(
        self,
        uri: str,
        cache_dir: str = "./cache",
        default_height: float = 0.25,
        default_velocity: float = 0.10,
        min_battery_v: float = 3.75,
        max_height_m: float = 0.45,
        max_abs_tilt_deg: float = 8.0,
    ):
        self.uri = uri
        self.cache_dir = cache_dir
        self.default_height = default_height
        self.default_velocity = default_velocity
        self.min_battery_v = min_battery_v
        self.max_height_m = max_height_m
        self.max_abs_tilt_deg = max_abs_tilt_deg
        self._drivers_initialized = False

    def init_drivers(self):
        if not self._drivers_initialized:
            cflib.crtp.init_drivers()
            self._drivers_initialized = True

    def _new_cf(self):
        return Crazyflie(rw_cache=self.cache_dir)

    def check_flow_deck(self, cf, timeout: float = 5.0) -> bool:
        event = Event()

        def cb(_, value_str):
            try:
                if int(value_str):
                    event.set()
            except Exception:
                pass

        cf.param.add_update_callback(group="deck", name="bcFlow2", cb=cb)
        time.sleep(1.0)
        return event.wait(timeout=timeout)

    def reset_estimator(self, cf):
        print("[Safety] Resetting Kalman estimator...")
        cf.param.set_value("kalman.resetEstimation", "1")
        time.sleep(0.2)
        cf.param.set_value("kalman.resetEstimation", "0")
        time.sleep(3.0)
        print("[Safety] Estimator reset done.")

    def emergency_stop_cf(self, cf):
        print("[Safety] Emergency stop setpoints.")
        for _ in range(60):
            cf.commander.send_stop_setpoint()
            time.sleep(0.02)

        try:
            cf.supervisor.send_arming_request(False)
        except Exception:
            pass

    def emergency_stop(self) -> Dict:
        self.init_drivers()

        with SyncCrazyflie(self.uri, cf=self._new_cf()) as scf:
            self.emergency_stop_cf(scf.cf)

        return {
            "status": "completed",
            "action": "emergency_stop",
        }

    def read_basic_telemetry(self, cf, duration: float = 2.0) -> Dict:
        data_store = {
            "battery_v": None,
            "pm_state": None,
            "z": None,
            "zrange": None,
            "roll": None,
            "pitch": None,
            "samples": 0,
        }

        event = Event()

        def cb(timestamp, data, logconf):
            data_store["battery_v"] = data.get("pm.vbat")
            data_store["pm_state"] = data.get("pm.state")
            data_store["z"] = data.get("stateEstimate.z")
            data_store["zrange"] = data.get("range.zrange")
            data_store["roll"] = data.get("stabilizer.roll")
            data_store["pitch"] = data.get("stabilizer.pitch")
            data_store["samples"] += 1
            event.set()

        logconf = LogConfig(name="SafetyTelemetry", period_in_ms=100)
        logconf.add_variable("pm.vbat", "float")
        logconf.add_variable("pm.state", "uint8_t")
        logconf.add_variable("stateEstimate.z", "float")
        logconf.add_variable("range.zrange", "uint16_t")
        logconf.add_variable("stabilizer.roll", "float")
        logconf.add_variable("stabilizer.pitch", "float")

        cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(cb)
        logconf.start()

        time.sleep(duration)

        logconf.stop()

        return data_store

    def preflight_check(self, cf) -> Dict:
        print("[Safety] Running preflight check...")

        if not self.check_flow_deck(cf, timeout=5.0):
            raise FlightSafetyError("Flow deck not detected. Abort.")

        self.reset_estimator(cf)

        telemetry = self.read_basic_telemetry(cf, duration=2.0)

        print("[Safety] Telemetry:", telemetry)

        if telemetry["samples"] < 5:
            raise FlightSafetyError("Not enough telemetry samples. Abort.")

        battery_v = telemetry["battery_v"]
        if battery_v is None or battery_v < self.min_battery_v:
            raise FlightSafetyError(
                f"Battery too low or unavailable: {battery_v}. "
                f"Required >= {self.min_battery_v} V."
            )

        z = telemetry["z"]
        if z is None:
            raise FlightSafetyError("stateEstimate.z unavailable. Abort.")

        if abs(z) > 0.08:
            raise FlightSafetyError(
                f"Initial stateEstimate.z abnormal: {z:.3f}. "
                "Keep drone still on ground and reset estimator."
            )

        zrange = telemetry["zrange"]
        if zrange is None or zrange <= 0:
            raise FlightSafetyError(
                f"range.zrange abnormal: {zrange}. "
                "Check Flow deck lens and ground texture."
            )

        roll = telemetry["roll"]
        pitch = telemetry["pitch"]

        if roll is None or pitch is None:
            raise FlightSafetyError("roll/pitch unavailable. Abort.")

        if abs(roll) > self.max_abs_tilt_deg or abs(pitch) > self.max_abs_tilt_deg:
            raise FlightSafetyError(
                f"Drone not level. roll={roll:.2f}, pitch={pitch:.2f}. Abort."
            )

        print("[Safety] Preflight check passed.")
        return telemetry

    def setup_height_guard(self, cf):
        guard = {
            "abort": False,
            "reason": None,
            "z": 0.0,
            "zrange": None,
        }

        def cb(timestamp, data, logconf):
            z = data.get("stateEstimate.z")
            zrange = data.get("range.zrange")

            guard["z"] = z
            guard["zrange"] = zrange

            if z is not None and z > self.max_height_m:
                guard["abort"] = True
                guard["reason"] = f"Height guard triggered: z={z:.3f} > {self.max_height_m}"

            if zrange is None or zrange <= 0:
                guard["abort"] = True
                guard["reason"] = f"Range guard triggered: zrange={zrange}"

        logconf = LogConfig(name="HeightGuard", period_in_ms=100)
        logconf.add_variable("stateEstimate.z", "float")
        logconf.add_variable("range.zrange", "uint16_t")

        cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(cb)

        return logconf, guard

    def get_status(self) -> Dict:
        self.init_drivers()

        status = {
            "uri": self.uri,
            "connected": False,
            "flow_deck": False,
            "telemetry": None,
            "estimator": None,
            "controller": None,
        }

        with SyncCrazyflie(self.uri, cf=self._new_cf()) as scf:
            cf = scf.cf
            status["connected"] = True
            status["flow_deck"] = self.check_flow_deck(cf, timeout=3.0)

            try:
                status["estimator"] = cf.param.get_value("stabilizer.estimator")
            except Exception:
                pass

            try:
                status["controller"] = cf.param.get_value("stabilizer.controller")
            except Exception:
                pass

            try:
                status["telemetry"] = self.read_basic_telemetry(cf, duration=2.0)
            except Exception as e:
                status["telemetry_error"] = str(e)

        return status

    def takeoff_land(self, height: float = None, hover_time: float = 2.0) -> Dict:
        self.init_drivers()

        height = height if height is not None else self.default_height

        if height > self.max_height_m:
            raise FlightSafetyError(
                f"Requested height {height} exceeds max safe height {self.max_height_m}"
            )

        with SyncCrazyflie(self.uri, cf=self._new_cf()) as scf:
            cf = scf.cf

            height_guard_log, guard = self.setup_height_guard(cf)

            try:
                self.preflight_check(cf)

                print("[Drone] Arming...")
                cf.supervisor.send_arming_request(True)
                time.sleep(1.0)

                height_guard_log.start()

                print(f"[Drone] Takeoff to {height}m, hover {hover_time}s.")

                with PositionHlCommander(
                    scf,
                    x=0.0,
                    y=0.0,
                    z=0.0,
                    default_height=height,
                    default_velocity=self.default_velocity,
                    controller=PositionHlCommander.CONTROLLER_PID,
                ):
                    end = time.time() + hover_time
                    while time.time() < end:
                        if guard["abort"]:
                            raise FlightSafetyError(guard["reason"])
                        time.sleep(0.05)

                print("[Drone] Landed.")

            except Exception:
                self.emergency_stop_cf(cf)
                raise

            finally:
                try:
                    height_guard_log.stop()
                except Exception:
                    pass

                self.emergency_stop_cf(cf)

        return {
            "status": "completed",
            "action": "takeoff_land",
            "height": height,
            "hover_time": hover_time,
        }

    def fly_waypoints(
        self,
        waypoints: List[Tuple[float, float, float]],
        velocity: float = None,
        hold_time: float = 1.0,
    ) -> Dict:
        self.init_drivers()

        velocity = velocity if velocity is not None else self.default_velocity

        for x, y, z in waypoints:
            if z > self.max_height_m:
                raise FlightSafetyError(
                    f"Waypoint z={z} exceeds max safe height {self.max_height_m}"
                )

        with SyncCrazyflie(self.uri, cf=self._new_cf()) as scf:
            cf = scf.cf

            height_guard_log, guard = self.setup_height_guard(cf)

            try:
                self.preflight_check(cf)

                print("[Drone] Arming...")
                cf.supervisor.send_arming_request(True)
                time.sleep(1.0)

                height_guard_log.start()

                with PositionHlCommander(
                    scf,
                    x=0.0,
                    y=0.0,
                    z=0.0,
                    default_height=self.default_height,
                    default_velocity=velocity,
                    controller=PositionHlCommander.CONTROLLER_PID,
                ) as pc:
                    time.sleep(1.0)

                    for x, y, z in waypoints:
                        if guard["abort"]:
                            raise FlightSafetyError(guard["reason"])

                        print(f"[Drone] go_to x={x:.2f}, y={y:.2f}, z={z:.2f}")
                        pc.go_to(x, y, z)

                        end = time.time() + hold_time
                        while time.time() < end:
                            if guard["abort"]:
                                raise FlightSafetyError(guard["reason"])
                            time.sleep(0.05)

                print("[Drone] Route completed and landed.")

            except Exception:
                self.emergency_stop_cf(cf)
                raise

            finally:
                try:
                    height_guard_log.stop()
                except Exception:
                    pass

                self.emergency_stop_cf(cf)

        return {
            "status": "completed",
            "action": "fly_waypoints",
            "waypoints": waypoints,
            "velocity": velocity,
            "hold_time": hold_time,
        }
