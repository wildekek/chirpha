"""Common routines/constants for bridge tests."""
from unittest import mock
from unittest.mock import patch
import threading
import json
import time
import re
from pathlib import Path

from chirpha.const import (
    CONF_APPLICATION_ID,
    CONF_MQTT_DISC,
)
import chirpha.start as chirpha
from chirpha.start import INTERNAL_CONFIG

from .patches import api, message, mqtt, set_size, get_size, insecure_channel

REGULAR_CONFIGURATION_FILE ="test_configuration.json"
PAYLOAD_PRINT_CONFIGURATION_FILE ="test_configuration_payload.json"
NO_APP_CONFIGURATION_FILE ="test_configuration_no_app.json"

# pytest tests/components/chirp/
# pytest tests/components/chirp/ --cov=homeassistant.components.chirp --cov-report term-missing -vv
# $PYTHONPATH rootfs/usr
# PATH  /home/modrisb/contributions/pijups/chirpstack/rootfs/usr/tests:/home/modrisb/.vscode/extensions/ms-python.python-2024.4.1/python_files/deactivate/bash:/home/modrisb/contributions/pijups/chirpstack/.venv/bin:/home/modrisb/.nvm/versions/node/v18.18.1/bin:/home/modrisb/.vscode/extensions/ms-python.python-2024.4.1/python_files/deactivate/bash:/home/modrisb/contributions/pijups/chirpstack/.venv/bin:/home/modrisb/contributions/pijups:/home/modrisb/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
# pytest chirp2mqtt/rootfs/usr/tests/ --cov=chirpha --cov-report term-missing
# pytest chirp2mqtt/rootfs/usr/tests/test_mqtt.py --cov=chirpha --cov-report term-missing --log-cli-level=DEBUG
# pytest chirp2mqtt/rootfs/usr/tests/ --cov=chirpha --cov-report term-missing --log-cli-level=DEBUG --capture=no

class run_chirp_ha:
    ch_tread = None
    cirpha_instance = None

    def __enter__(self):
        self.cirpha_instance = chirpha.run_chirp_ha()
        self.ch_tread = threading.Thread(target=self.cirpha_instance.main)
        self.ch_tread.start()
        return self

    def __exit__(self, *args):
        if self.ch_tread.is_alive():
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).close()
        self.ch_tread.join()

@mock.patch("chirpha.grpc.api", new=api)
@mock.patch("chirpha.grpc.grpc.insecure_channel", new=insecure_channel)
@mock.patch("chirpha.mqtt.mqtt", new=mqtt)
def chirp_setup_and_run_test(run_test_case, conf_file=REGULAR_CONFIGURATION_FILE, test_params=dict(), a_live_at_end=True, kill_at_end=False, check_msg_queue=True):
    """Execute test case in standard configuration environment with grpc/mqtt mocks."""
    module_dir = Path(globals().get("__file__", "./_")).absolute().parent
    full_path_to_conf_file =str(module_dir) + '/' + conf_file

    with open(full_path_to_conf_file, 'r') as file:
        config = json.load(file)
    config = config | INTERNAL_CONFIG

    set_size(**test_params)
    with patch("chirpha.start.CONFIGURATION_FILE", new=full_path_to_conf_file):
        with run_chirp_ha() as ch:
            time.sleep(0.01)
            if ch.ch_tread.is_alive():
                mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
                if ch.ch_tread.is_alive():
                    mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(f"{config.get(CONF_MQTT_DISC)}/status", "online")
                    mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
                    if check_msg_queue:
                        ha_online = count_messages(r'homeassistant/status', r'online', keep_history=True)
                        bridge_online = count_messages(r'.*/bridge/status', r'online', keep_history=True)
                        bridge_config = count_messages(r'.*', r'"name": "Chirp2MQTT Bridge"', keep_history=True)
                        messages = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
                        assert ha_online == 1   # 1 message sent from test environment
                        assert bridge_config == 2   # 2 messages sent to register bridge
                        assert bridge_online == 1   # 1 online message sent when bridge is registered

                    if run_test_case:
                        run_test_case(config)

                    mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
                    assert a_live_at_end == ch.ch_tread.is_alive()
                    if ch.ch_tread.is_alive():
                        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("sensors") * get_size("idevices")
                        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
                        if kill_at_end:
                            ch.cirpha_instance.stop_chirp_ha(None, None)
                            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
            else:
                assert not a_live_at_end

def reload_devices(config):
    """Reload devices from ChirpStack server and wait for activity completion."""
    restart_topic = f"application/{config.get(CONF_APPLICATION_ID)}/bridge/restart"
    mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(restart_topic, "")
    mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()

def count_messages(topic, payload, keep_history=False):
    """Count posted mqtt messages that matche topic and payload filters."""
    messages = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=keep_history)
    count = 0
    for message in messages:
        mi_topic = re.search(topic, message[0])
        if payload:
            mi_payload = re.search(payload, message[1])
            if mi_topic and mi_payload:
                count += 1
        else:
            if mi_topic:
                count += 1

    return count

def check_for_no_registration(config):
    """Check for no mqtt registration messages with assertion."""
    sensor_configs = count_messages(r'/config', r'"via_device": "chirp2mqtt_bridge_', keep_history=True)
    assert sensor_configs == 0  #   check for 0 devices/sensors registered
