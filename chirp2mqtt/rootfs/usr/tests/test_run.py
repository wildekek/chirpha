"""Test the ChirpStack LoRa integration execution with sending MQTT device messages."""

import time
import logging

from chirpha.const import BRIDGE_CONF_COUNT, CONF_APPLICATION_ID
from tests import common

from .patches import get_size, mqtt, set_size
from tests.common import PAYLOAD_PRINT_CONFIGURATION_FILE
#   su-exec postgres psql
#   \c chirpstack
#   DELETE FROM api_key WHERE created_at < to_date('2025-05-01', 'YYYY-MM-DD');

def test_ha_status_received(caplog):
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
        # expecting config message per sensor + 1 bridge, 1 removal, 1 sensor data initialization message, 1 bridge state message
        configs = common.count_messages(r'/config$', r' ', keep_history=True)    # to be received as subscribed
        removals = common.count_messages_with_no_payload(r'/config$', keep_history=True)    # to be received as subscribed
        status_online = common.count_messages(r'/status$', None, keep_history=True)    # to be received as subscribed
        up_msg = common.count_messages(r'/up$', None, keep_history=True)    # to be received as subscribed
        restart = common.count_messages(r'/restart$', None, keep_history=True)    # to be received as subscribed
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics)  == configs + removals + status_online + up_msg + restart
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

    common.chirp_setup_and_run_test(caplog, run_test_ha_status_received, conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE)


def test_ha_status_received_with_debug_log(caplog):
    """Test for HA status message received with debug log enabled."""

    def run_test_ha_status_received_with_debug_log(config):
        set_size(devices=1, codec=0)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        common.reload_devices(config)
        time.sleep(0.1)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("sensors") * get_size("idevices")  # 4 sensors per codec=0 device
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        # expecting config message per sensor + 1 bridge, 1 removal, 1 sensor data initialization message, 1 bridge state message
        configs = common.count_messages(r'/config$', r' ', keep_history=True)    # to be received as subscribed
        removals = common.count_messages_with_no_payload(r'/config$', keep_history=True)    # to be received as subscribed
        status_online = common.count_messages(r'/status$', None, keep_history=True)    # to be received as subscribed
        up_msg = common.count_messages(r'/up$', None, keep_history=True)    # to be received as subscribed
        restart = common.count_messages(r'/restart$', None, keep_history=True)    # to be received as subscribed
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics)  == configs + removals + status_online + up_msg + restart
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

    common.chirp_setup_and_run_test(caplog, run_test_ha_status_received_with_debug_log, conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE )


def test_payload_join(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_payload_join(config):
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        # send cur message for each device to simulate retain=True, check for timestamp after bridge initialization - to be ignored
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/cur"
            msg = f'{{"time_stamp":{time.time()+400},"batteryLevel": 76,"rxInfo":[{{"location":{{"altitude":11}}}}]}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        no_of_cur_msgs = common.count_messages(r'/device/.*/cur$', None, keep_history=True)    # to be received as subscribed
        no_of_up_msgs = common.count_messages(r'/device/.*/up$', None, keep_history=True)    # should not show up due to time stamp
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 0
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics) == no_of_cur_msgs + no_of_up_msgs # should be just cur/up pairs per device
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices
        # send cur message for each device to simulate retain=True, timestamp must be before bridge initialization
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/cur"
            msg = f'{{"time_stamp":{time.time()-400},"batteryLevel": 76}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        no_of_cur_msgs = common.count_messages(r'/device/.*/cur$', None, keep_history=True)    # message just sent to initiate values restore
        no_of_up_msgs = common.count_messages(r'/device/.*/up$', None, keep_history=True)    # message to restore previous values
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 1
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert len(config_topics) == no_of_cur_msgs + no_of_up_msgs # should be just cur/up pairs per device
        assert len(config_topics) == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices * 2
        #
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/up"
            msg = f'{{"batteryLevel": 77,"rxInfo":[{{"location":{{"altitude":12}}}}]}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        no_of_up_msgs = common.count_messages(r'/device/.*/event/up$', None, keep_history=True)    # new value come in
        no_of_cur_msgs = common.count_messages(r'/device/.*/event/cur$', r'"batteryLevel": 77, "rxInfo": \[{"location": {"altitude": 12}}\], ', keep_history=True)    # issued to save values
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 1
        assert len(config_topics) == no_of_cur_msgs + no_of_up_msgs # should be just cur/up pairs per device
        #
        for i in range(0, mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices):
            dev_eui = f"dev_eui{i}"
            topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/up"
            msg = '{"object":{"'+f"sensor{i}"+'":13}}'
            mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        no_of_up_msgs = common.count_messages(r'/device/.*/event/up$', None, keep_history=True)    # new value come in
        no_of_cur_msgs = common.count_messages(r'/device/.*/event/cur$', r'{"object": {"sensor0": 13}, "batteryLevel": 77, "rxInfo": \[{"location": {"altitude": 12}}\], ', keep_history=True)    # issued to save values
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 1
        assert len(config_topics) == no_of_cur_msgs + no_of_up_msgs # should be just cur/up pairs per device

    common.chirp_setup_and_run_test(caplog, run_test_payload_join, test_params=dict(devices=1, codec=0), conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)
