"""Test the ChirpStack LoRa integration execution with sending MQTT device messages."""

import time
import logging

from chirpha.const import BRIDGE_CONF_COUNT, CONF_APPLICATION_ID
from tests import common

from .patches import get_size, mqtt, set_size
from tests.common import PAYLOAD_PRINT_CONFIGURATION_FILE, REGULAR_CONFIGURATION_FILE, REGULAR_CONFIGURATION_FILE_INFO
from tests.common import REGULAR_CONFIGURATION_FILE_ERROR, CONF_MQTT_DISC, WITH_DELAY_CONFIGURATION_FILE
from tests.common import REGULAR_CONFIGURATION_FILE_INFO_NO_MQTT, REGULAR_CONFIGURATION_FILE_DEBUG_NO_MQTT
from tests.common import REGULAR_CONFIGURATION_FILE_WRONG_LOG_LEVEL

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
        assert configs == get_size("sensors") * get_size("devices")
        assert status_online == 0
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
        assert configs == get_size("sensors") * get_size("devices")
        assert status_online == 0
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

def test_log_levels_debug(caplog):
    """Test for HA status message received with debug log enabled."""
    common.chirp_setup_and_run_test(caplog, None, conf_file=REGULAR_CONFIGURATION_FILE, allowed_msg_level=logging.ERROR )
    is_printed = 0
    for record in caplog.records:
        assert record.levelno >= logging.DEBUG
        if record.levelno == logging.DEBUG: is_printed += 1
    assert is_printed > 0

def test_log_levels_info(caplog):
    """Test for HA status message received with debug log enabled."""
    common.chirp_setup_and_run_test(caplog, None, conf_file=REGULAR_CONFIGURATION_FILE_INFO, allowed_msg_level=logging.ERROR )
    is_printed = 0
    for record in caplog.records:
        assert record.levelno >= logging.INFO
        if record.levelno == logging.INFO: is_printed += 1
    assert is_printed > 0

def test_log_levels_error(caplog):
    """Test for HA status message received with debug log enabled."""
    common.chirp_setup_and_run_test(caplog, None, test_params=dict(devices=1, codec=3), conf_file=REGULAR_CONFIGURATION_FILE_ERROR, allowed_msg_level=logging.ERROR )
    is_printed = 0
    for record in caplog.records:
        assert record.levelno >= logging.ERROR
        if record.levelno == logging.ERROR: is_printed += 1
    assert is_printed > 0

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
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 0
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
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 1
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

def test_payload_join_no_ha_online(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_payload_join_no_ha_online(config):
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
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published()
        assert no_of_cur_msgs == 1 and no_of_up_msgs == 0
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

    common.chirp_setup_and_run_test(caplog, run_test_payload_join_no_ha_online, test_params=dict(devices=1, codec=0), conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING, no_ha_online=True)

def test_payload_join_no_ha_online_ext(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_payload_join_no_ha_online_ext(config):
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(f"{config.get(CONF_MQTT_DISC)}/status", "online")
        time.sleep(0.1)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        no_ha_online = common.count_messages(r'^homeassistant/status$', r"online", keep_history=True)    # to be received as subscribed
        assert no_ha_online == 1

    common.chirp_setup_and_run_test(caplog, run_test_payload_join_no_ha_online_ext, test_params=dict(devices=1, codec=0), conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING, no_ha_online=True)

def test_ha_offline_online(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_ha_offline_online(config):
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(f"{config.get(CONF_MQTT_DISC)}/status", "offline")
        time.sleep(0.1)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(f"{config.get(CONF_MQTT_DISC)}/status", "online")
        time.sleep(0.1)
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        no_ha_online = common.count_messages(r'^homeassistant/status$', r"online", keep_history=True)    # to be received as subscribed
        no_ha_offline = common.count_messages(r'^homeassistant/status$', r"offline", keep_history=True)    # to be received as subscribed
        no_of_conf_msgs = common.count_messages(r'dev_eui.*/config$', f'{config[CONF_APPLICATION_ID]}', keep_history=True)    # new value come in
        assert no_ha_online == 2
        assert no_ha_offline == 1
        assert no_of_conf_msgs == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * 2

    common.chirp_setup_and_run_test(caplog, run_test_ha_offline_online, test_params=dict(devices=1, codec=0), conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)

def test_ha_online_rec(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_ha_online_rec(config):
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        no_ha_online = common.count_messages(r'^homeassistant/status$', r"online", keep_history=True)    # to be received as subscribed
        no_of_conf_msgs = common.count_messages(r'dev_eui.*/config$', f'{config[CONF_APPLICATION_ID]}', keep_history=True)    # new value come in
        assert no_ha_online == 1
        assert no_of_conf_msgs == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors
        assert "HA online, publishing bridge setup 'configure' message" in caplog.text
        assert "timeout expired, but no HA online message received" not in caplog.text

    common.chirp_setup_and_run_test(caplog, run_test_ha_online_rec, test_params=dict(devices=1, codec=0), conf_file=WITH_DELAY_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)

def test_no_mqtt_short_error_message(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_no_mqtt_short_error_message(config):
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        no_ha_online = common.count_messages(r'^homeassistant/status$', r"online", keep_history=True)    # to be received as subscribed
        no_of_conf_msgs = common.count_messages(r'dev_eui.*/config$', f'{config[CONF_APPLICATION_ID]}', keep_history=True)    # new value come in
        assert no_ha_online == 1
        assert no_of_conf_msgs == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors
        assert "Chirp failed:" in caplog.text
        assert "Traceback (most recent call last):" not in caplog.text

    common.chirp_setup_and_run_test(caplog, run_test_no_mqtt_short_error_message, test_params=dict(mqtt=0, devices=1, codec=0), conf_file=REGULAR_CONFIGURATION_FILE_INFO_NO_MQTT, allowed_msg_level=logging.ERROR, a_live_at_end=False)

def test_no_mqtt_long_error_message(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_no_mqtt_long_error_message(config):
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        no_ha_online = common.count_messages(r'^homeassistant/status$', r"online", keep_history=True)    # to be received as subscribed
        no_of_conf_msgs = common.count_messages(r'dev_eui.*/config$', f'{config[CONF_APPLICATION_ID]}', keep_history=True)    # new value come in
        assert no_ha_online == 1
        assert no_of_conf_msgs == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors
        assert "Chirp failed:" in caplog.text
        assert "Traceback (most recent call last):" in caplog.text

    common.chirp_setup_and_run_test(caplog, run_test_no_mqtt_long_error_message, test_params=dict(mqtt=0, devices=1, codec=0), conf_file=REGULAR_CONFIGURATION_FILE_DEBUG_NO_MQTT, allowed_msg_level=logging.ERROR, a_live_at_end=False)

def test_wrong_log_level(caplog):
    """Test payload join for array data with more than 1 sublevel."""

    def run_test_wrong_log_level(config):
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).wait_empty_queue()
        config_topics = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        no_ha_online = common.count_messages(r'^homeassistant/status$', r"online", keep_history=True)    # to be received as subscribed
        no_of_conf_msgs = common.count_messages(r'dev_eui.*/config$', f'{config[CONF_APPLICATION_ID]}', keep_history=True)    # new value come in
        assert no_ha_online == 1
        assert no_of_conf_msgs == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors
        assert "Wrong log level specified" in caplog.text

    common.chirp_setup_and_run_test(caplog, run_test_wrong_log_level, test_params=dict(devices=1, codec=0), conf_file=REGULAR_CONFIGURATION_FILE_WRONG_LOG_LEVEL, allowed_msg_level=logging.WARNING)
