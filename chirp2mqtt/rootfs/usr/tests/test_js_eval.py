"""Test the Wan integration gRPC interface class."""

from tests import common
import time

from .patches import get_size, mqtt, set_size
from tests.common import (REGULAR_CONFIGURATION_FILE, PAYLOAD_PRINT_CONFIGURATION_FILE, NO_APP_CONFIGURATION_FILE)

def test_codec_prologue_noissues():
    """Test codec with issues in prologue, no devices to be installed."""

    def run_test_codec_prologue_noissues(config):
        #set_size(devices=1, codec=17)  # function name missing
        #common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check

    common.chirp_setup_and_run_test(run_test_codec_prologue_noissues, test_params=dict(devices=1, codec=17))


def test_codec_prologue_issues():
    """Test codec with issues in prologue, no devices to be installed."""

    def run_test_codec_prologue_issues(config):
        #set_size(devices=1, codec=18)  # function name missing
        #common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check

    common.chirp_setup_and_run_test(run_test_codec_prologue_issues, test_params=dict(devices=1, codec=18))
