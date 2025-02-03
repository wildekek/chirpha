"""Test the Wan integration gRPC interface class."""

from tests import common
import time
from unittest import mock

from .patches import get_size, mqtt, set_size, dukpy

def test_faulty_codec():
    """Test faulty codec - devices are not installed."""

    common.chirp_setup_and_run_test(common.check_for_no_registration, test_params=dict(devices=1, codec=3))

@mock.patch("chirpha.grpc.dukpy", new=dukpy)
def test_faulty_json():
    """Test faulty codec json: conversion to json mocked false making descriptor ignored """

    common.chirp_setup_and_run_test(common.check_for_no_registration, test_params=dict(devices=1, codec=19))

def test_codec_with_single_q_strings():
    """Test codec with ' as string encloser - devices to be installed."""
    def run_test_codec_with_single_q_strings(config):
        msg_count = common.count_messages(r'/config', r'vendor0', keep_history=True)
        assert msg_count == 1
        msg_count = common.count_messages(r'/config', r'model1', keep_history=True)
        assert msg_count == 1
        msg_count = common.count_messages(r'/config', r'{{ value_json.object.counter }}', keep_history=True)
        assert msg_count == 1

    common.chirp_setup_and_run_test(run_test_codec_with_single_q_strings, test_params=dict(devices=1, codec=16) )


def test_with_devices_disabled():
    """Test disabled devices are listed - no devices to be installed."""

    common.chirp_setup_and_run_test(common.check_for_no_registration, test_params=dict(disabled=True))


def test_codec_prologue_issues():
    """Test codec with issues in prologue, no devices to be installed."""

    def run_test_codec_prologue_issues(config):
        common.check_for_no_registration(config)
        set_size(devices=1, codec=12)  # return statement missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        common.check_for_no_registration(config)
        set_size(devices=1, codec=13)  # } after return statement missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        common.check_for_no_registration(config)

    common.chirp_setup_and_run_test(run_test_codec_prologue_issues, test_params=dict(devices=1, codec=11))


def test_codec_with_comment():
    """Test codec with comments in body."""

    def run_test_codec_with_comment(config):
        sensor_configs = common.count_messages(r'/config', r'"via_device": "chirp2mqtt_bridge_', keep_history=False)
        assert sensor_configs == 1
        set_size(devices=1, codec=14)  # incorrect comment, codec should fail
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        common.check_for_no_registration(config)

    common.chirp_setup_and_run_test(run_test_codec_with_comment, test_params=dict(devices=1, codec=4))
