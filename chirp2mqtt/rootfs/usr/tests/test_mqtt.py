"""Test the ChirpStack LoRa integration MQTT integration class."""

import time

from chirpha.const import BRIDGE_CONF_COUNT, CONF_APPLICATION_ID
from tests import common

from .patches import get_size, mqtt, set_size
from tests.common import PAYLOAD_PRINT_CONFIGURATION_FILE

def test_extended_debug_level():
    """Test run with extended debug enabled."""

    def run_test_level_names_with_indexes(config):
        common.reload_devices(config)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("idevices") * get_size("sensors")

    common.chirp_setup_and_run_test(run_test_level_names_with_indexes)


def test_level_names_with_indexes():
    """Test run with values description with indexes."""
    def run_test_level_names_with_indexes(config):
        indexed_configs = common.count_messages(r'/config', r'"value_template":\s*"{{\s*value_json\..*\[.*\]\s*}}"', keep_history=False)
        assert indexed_configs == 2

    common.chirp_setup_and_run_test(run_test_level_names_with_indexes, test_params=dict(devices=1, codec=5))

def test_values_template_default():
    """Test if default value_template is added to configuration."""
    def run_test_values_template_default(config):
        indexed_configs = common.count_messages(r'/config', r'value_json.object.counter', keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(run_test_values_template_default, test_params=dict(devices=1, codec=6))


def test_explicit_integration_setting():
    """Test run with explicit integration set in codec js."""
    def run_test_explicit_integration_setting(config):
        indexed_configs = common.count_messages(r'/climate/.*/config', None, keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(run_test_explicit_integration_setting, test_params=dict(devices=1, codec=7))


def test_no_device_class():
    """Test run with no explicit device class set in codec js."""
    def run_test_no_device_class(config):
        indexed_configs = common.count_messages(r'/sensor/.*/config', r"device_class", keep_history=False)
        assert indexed_configs == 0

    common.chirp_setup_and_run_test(run_test_no_device_class, test_params=dict(devices=1, codec=8))


def test_wrong_device_class():
    """Test run with unknown device class set in codec js."""
    def run_test_wrong_device_class(config):
        indexed_configs = common.count_messages(r'/sensor/.*/config', None, keep_history=False)
        assert indexed_configs == 1
        indexed_configs = common.count_messages(r'/sensor/.*/config', r"device_class", keep_history=False)
        assert indexed_configs == 0

    common.chirp_setup_and_run_test(run_test_wrong_device_class, test_params=dict(devices=1, codec=9))

def test_command_topic():
    """Test run with command topic set in codec js."""
    def run_test_command_topic(config):
        indexed_configs = common.count_messages(r'/config', r'"command_topic".*/down', keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(run_test_command_topic, test_params=dict(devices=1, codec=10))


def test_humidifier_dev_class():
    """Test run with humidifier device class in codec js.."""
    def run_test_humidifier_dev_class(config):
        indexed_configs = common.count_messages(r'/humidifier/.*/config', None, keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(run_test_humidifier_dev_class, test_params=dict(devices=1, codec=15))


def test_ha_status_received():
    """Test for HA status message received."""

    def run_test_ha_status_received(config):
        set_size(devices=1, codec=0)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        common.reload_devices(config)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("sensors") * get_size(
            "idevices"
        )  # 4 sensors per codec=0 device
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        # expecting config message per sensor + 1 bridge, 1 removal, 1 sensor data initialization message, 1 bridge state message
        configs = removals = status_online = up_msg = 0
        for msg in config_topics:
            sub_topics = msg[0].split("/")
            if sub_topics[-1] == "config":
                if msg[1] is not None:
                    configs += 1
                else:
                    removals += 1
            if sub_topics[-1] == "status":
                status_online += 1
            if sub_topics[-1] == "up":
                up_msg += 1
        assert len(config_topics) -1 == configs + removals + status_online + up_msg # -1 for restart topic
        assert configs == get_size("sensors") * get_size("devices") + BRIDGE_CONF_COUNT
        assert status_online == 1
        # simulate incoming values restore mqtt message. This should show up as up event for recently registered devices and
        # nothing for non-registered devices
        for i in range(
            0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices + 1
        ):  # +1 to ensure message for non-registered device
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/cur"
            msg = f'{{"time_stamp":{time.time()-200}}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        # check for topic count matching device count
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices + 1
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/up"
            msg = f'{{"batteryLevel": 93,"object": {{"{dev_eui}": 9}},"rxInfo": [{{"rssi": -75,"snr": 6,"location": {{"latitude": 56.9,"longitude": 24.1}}}}]}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices
        set_size(devices=0, codec=0)
        common.reload_devices(config)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("sensors") * get_size("devices")

    common.chirp_setup_and_run_test(run_test_ha_status_received, conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE)


def test_ha_status_received_with_debug_log():
    """Test for HA status message received with debug log enabled."""

    def run_test_ha_status_received_with_debug_log(config):
        set_size(devices=1, codec=0)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        common.reload_devices(config)
        time.sleep(0.1)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("sensors") * get_size("idevices")  # 4 sensors per codec=0 device
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        # expecting config message per sensor + 1 bridge, 1 removal, 1 sensor data initialization message, 1 bridge state message
        configs = removals = status_online = up_msg = restart = 0
        for msg in config_topics:
            sub_topics = msg[0].split("/")
            if sub_topics[-1] == "config":
                if msg[1] is not None:
                    configs += 1
                else:
                    removals += 1
            if sub_topics[-1] == "status":
                status_online += 1
            if sub_topics[-1] == "up":
                up_msg += 1
            if sub_topics[-1] == "restart":
                restart += 1
        assert len(config_topics)  == configs + removals + status_online + up_msg + restart # - 1 restart topic
        assert configs == get_size("sensors") * get_size("devices") + BRIDGE_CONF_COUNT
        assert status_online == 1
        for i in range(
            0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices + 1
        ):  # +1 to ensure message for non-registered device
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/cur"
            msg = f'{{"time_stamp":{time.time()-200}}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        # check for topic count matching device count
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices + 1
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/up"
            msg = f'{{"batteryLevel": 93,"object": {{"{dev_eui}": 9}},"rxInfo": [{{"rssi": -75,"snr": 6,"location": {{"latitude": 56.9,"longitude": 24.1}}}}]}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices
        set_size(devices=0, codec=0)
        common.reload_devices(config)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == 0

    common.chirp_setup_and_run_test(run_test_ha_status_received_with_debug_log, conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE )


def test_payload_join():
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_payload_join(config):
        set_size(devices=1, codec=0)
        common.reload_devices(config)
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("sensors") * get_size("idevices")  # 4 sensors per codec=0 device
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/cur"
            msg = f'{{"time_stamp":{time.time()-200},"rxInfo":[{{"location":{{"altitude":11}}}}]}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices

    common.chirp_setup_and_run_test(run_test_payload_join)
