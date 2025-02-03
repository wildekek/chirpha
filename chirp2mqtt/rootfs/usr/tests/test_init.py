"""Test the ChirpStack LoRaWan integration initilization path initiated from start.py."""
from tests import common

from .patches import get_size, mqtt, set_size
from tests.common import NO_APP_CONFIGURATION_FILE

def test_entry_setup_unload():
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(None)

def test_grpc_connection_failure():
    """Test app exits in case of grpc failure."""

    common.chirp_setup_and_run_test(None, test_params=dict(grpc=0), a_live_at_end=False)

def test_setup_with_no_tenants():
    """Test if missing tenant has been creted and app is up."""

    common.chirp_setup_and_run_test(None, test_params=dict(tenants=0), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE)

def test_setup_with_autoselected_tenant_no_apps():#ffffff
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(None, test_params=dict(tenants=1, applications=0), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE)

def test_setup_with_tenant_selection_no_apps():
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(None, test_params=dict(applications=0), a_live_at_end=True)

def test_setup_with_auto_tenant_auto_apps():
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(None, test_params=dict(tenants=1, applications=1), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE)

def test_setup_with_auto_tenant_apps_selection():
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(None, test_params=dict(tenants=1, applications=2), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE)


def test_setup_with_auto_tenant_auto_apps_mqtt_fail():
    """Test if chirpha gracefully exits in case of mqtt connection failure."""

    common.chirp_setup_and_run_test(None, test_params=dict(tenants=1, mqtt=0), a_live_at_end=False)


def test_setup_with_auto_tenant_auto_apps_mqtt():
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(None, test_params=dict(tenants=1), a_live_at_end=True)

def test_thread_kill():
    """Test forced exit from chirpha."""

    def run_test_thread_kill(config):
        set_size(codec=7)
        common.reload_devices(config)
        assert get_size("devices") * get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors

    common.chirp_setup_and_run_test(run_test_thread_kill, kill_at_end=True)

def test_setup_with_failing_mqtt_publish():
    """Test if chirpha gracefully exits in case of mqtt publish failure."""

    common.chirp_setup_and_run_test(None, test_params=dict(publish=0), a_live_at_end=False, check_msg_queue=False)
