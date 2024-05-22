"""Test the Wan integration gRPC interface class."""

from tests import common
import time

from .patches import get_size, mqtt, set_size
from tests.common import (REGULAR_CONFIGURATION_FILE, PAYLOAD_PRINT_CONFIGURATION_FILE, NO_APP_CONFIGURATION_FILE)

def test_faulty_codec():
    """Test faulty codec - devices are not installed."""

    common.chirp_setup_and_run_test(None, test_params=dict(devices=1, codec=3))

def test_codec_with_single_q_strings():
    """Test codec with ' as string encloser - devices to be installed."""

    common.chirp_setup_and_run_test(None, test_params=dict(devices=1, codec=16) )


def test_with_devices_disabled():
    """Test disabled devices are listed - no devices to be installed."""

    common.chirp_setup_and_run_test(None, test_params=dict(disabled=True))


def test_codec_prologue_issues():
    """Test codec with issues in prologue, no ddevices to be installed."""

    def run_test_codec_prologue_issues(config):
        set_size(devices=1, codec=11)  # function name missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        set_size(devices=1, codec=12)  # return statement missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        set_size(devices=1, codec=13)  # { after return statement missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check

    common.chirp_setup_and_run_test(run_test_codec_prologue_issues)


def test_codec_with_comment():
    """Test codec with comments in body."""

    def run_test_codec_with_comment(config):
        set_size(devices=1, codec=4)  # correct comment, codec correct
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        set_size(devices=1, codec=14)  # incorrect comment, codec should fail
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check

    common.chirp_setup_and_run_test(run_test_codec_with_comment)
