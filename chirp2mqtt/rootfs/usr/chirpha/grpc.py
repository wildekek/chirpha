"""The Chirpstack LoRaWan integration - grpc interface to ChirpStack server."""
from __future__ import annotations

import json
import logging
import subprocess
import dukpy

from chirpstack_api import api
import grpc

from .const import CONF_API_PORT, CONF_API_SERVER, CONF_APPLICATION_ID, CHIRPSTACK_TENANT, CHIRPSTACK_APPLICATION


_LOGGER = logging.getLogger(__name__)


class ChirpGrpc:
    """Chirp2MQTT grpc interface support."""

    def __init__(self, config, version) -> None:
        """Open connection to ChirpStack api server."""
        self._config = config
        self._version = version
        self._application_id = self._config.get(CONF_APPLICATION_ID)
        self._channel = grpc.insecure_channel(
            f"{self._config.get(CONF_API_SERVER)}:{self._config.get(CONF_API_PORT)}"
        )
        bearer = subprocess.run(["chirpstack", "-c", "/etc/chirpstack", "create-api-key", "--name", "chirpha"], capture_output=True, text=True).stdout.split("token: ")[-1].rstrip("\n")
        self._auth_token = [("authorization", f"Bearer {bearer}")]
        _LOGGER.info(
            "gRPC channel opened for %s:%s",
            self._config.get(CONF_API_SERVER),
            self._config.get(CONF_API_PORT),
        )
        if not self.is_valid_app_id( self._application_id):
            tenants_on_chirp = self.get_chirp_tenants()
            if len(tenants_on_chirp) == 0:
                tenant = api.TenantServiceStub(self._channel)
                createTenantReq = api.CreateTenantRequest()
                createTenantReq.tenant.name = CHIRPSTACK_TENANT
                createTenantReq.tenant.can_have_gateways = True
                createTenantReq.tenant.max_gateway_count = 1
                tenantResp = tenant.Create(createTenantReq, metadata=self._auth_token)
                _LOGGER.info("Tenant %s (id %s) created", createTenantReq.tenant.name, tenantResp.id)
                tenants_on_chirp = self.get_chirp_tenants()
            for tenant, id in tenants_on_chirp.items():
                tenant_id = id
                break
            applications_on_chirp = self.get_tenant_applications(tenant_id)
            if len(applications_on_chirp) == 0:
                application = api.ApplicationServiceStub(self._channel)
                createApplicationReq = api.CreateApplicationRequest()
                createApplicationReq.application.name = CHIRPSTACK_APPLICATION
                createApplicationReq.application.tenant_id = tenant_id
                applicationResp = application.Create(createApplicationReq, metadata=self._auth_token)
                _LOGGER.info("Application %s (id %s, tenant %s) created", createApplicationReq.application.name, tenant, applicationResp.id)
                applications_on_chirp = self.get_tenant_applications(tenant_id)
            for application, id in applications_on_chirp.items():
                application_id = id
                break
            _LOGGER.warning("%s is not valid application ID, using %s (tenant %s, application %s)", self._application_id, application_id, tenant, application)
            self._application_id = application_id
        self.js_interpreter = dukpy.JSInterpreter()
        _LOGGER.info("ChirpStack application ID %s", self._application_id)

    def get_chirp_tenants(self):
        """Get tenant list from api server, build name/id dictionary and return."""
        tenants = api.TenantServiceStub(self._channel)
        listTenantsReq = api.ListTenantsRequest()
        tenantsResp = tenants.List(listTenantsReq, metadata=self._auth_token)
        listTenantsReq.limit = tenantsResp.total_count
        tenantsResp = tenants.List(listTenantsReq, metadata=self._auth_token)
        return {tenant.name: tenant.id for tenant in tenantsResp.result}

    def get_tenant_applications(self, tenant_id):
        """Get applications list from api server, build name/id dictionary and return."""
        applications = api.ApplicationServiceStub(self._channel)
        listApplicationsReq = api.ListApplicationsRequest()
        listApplicationsReq.tenant_id = tenant_id
        applicationsResp = applications.List(
            listApplicationsReq, metadata=self._auth_token
        )
        listApplicationsReq.limit = applicationsResp.total_count
        applicationsResp = applications.List(
            listApplicationsReq, metadata=self._auth_token
        )
        return {
            application.name: application.id for application in applicationsResp.result
        }

    def is_valid_app_id(self, application_id):
        application = api.ApplicationServiceStub(self._channel)
        applicationReq = api.GetApplicationRequest()
        applicationReq.id = application_id
        try:
            application.Get( applicationReq, metadata=self._auth_token )
        except Exception:
            return False
        return True

    def get_chirp_app_devices(self):
        """Get application's devices from api server."""
        devices = api.DeviceServiceStub(self._channel)
        listDevicesReq = api.ListDevicesRequest()
        listDevicesReq.application_id = self._application_id
        devicesResp = devices.List(listDevicesReq, metadata=self._auth_token)
        listDevicesReq.limit = devicesResp.total_count
        devicesResp = devices.List(listDevicesReq, metadata=self._auth_token)
        return devicesResp.result

    #   [desc.name for desc, val in deviceReq.ListFields()]
    def get_chirp_device(self, dev_eui):
        """Get device details by dev_eui from api server."""
        device = api.DeviceServiceStub(self._channel)
        deviceReq = api.GetDeviceRequest()
        deviceReq.dev_eui = dev_eui
        device_details = device.Get(deviceReq, metadata=self._auth_token)
        return device_details

    def get_chirp_device_profile(self, device_profile_id):
        """Get device profile details by id from api server."""
        profile = api.DeviceProfileServiceStub(self._channel)
        listDevicesReq = api.GetDeviceProfileRequest()
        listDevicesReq.id = device_profile_id
        return profile.Get(listDevicesReq, metadata=self._auth_token)

    def isDeviceDisbled(self, dev_eui):
        """Check if device with dev_eui is enabled by reading device details from api server."""
        device = self.get_chirp_device(dev_eui)
        return device.device.is_disabled

    def close(self):
        """Close grpc channel."""
        self._channel.close()

    def get_current_device_entities(self):
        """Get enabled device list from api server."""
        devices_list = []
        devices = self.get_chirp_app_devices()
        for device in devices:
            if self.isDeviceDisbled(device.dev_eui):
                continue
            profile = self.get_chirp_device_profile(device.device_profile_id)
            discovery = None
            try:
                discovery = self.js_interpreter.evaljs(profile.device_profile.payload_codec_script+"; JSON.stringify(getHaDeviceInfo())")
                print("CODEC0 ", discovery)
            except Exception as error:  # pylint: disable=broad-exception-caught
                _LOGGER.debug(
                    "Profile %s discovery codec script error '%s', source code '%s' converted to json '%s'",
                    profile.device_profile.name,
                    str(error),
                    profile.device_profile.payload_codec_script,
                    discovery,
                )
                discovery = None
            #print("CODEC+", profile.device_profile.name, discovery)   ###########################
            #discovery_json = get_ha_descriptor(
            #    profile.device_profile.payload_codec_script
            #)
            #print("CODEC ", profile.device_profile.name, discovery_json[0])   ###########################
            #discovery = discovery_json[0]
            if discovery:
                try:
                    discovery = json.loads(discovery)
                except Exception as error:  # pylint: disable=broad-exception-caught
                    _LOGGER.debug(
                        "Profile %s discovery codec script error '%s', source code '%s' converted to json '%s'",
                        profile.device_profile.name,
                        str(error),
                        profile.device_profile.payload_codec_script,
                        discovery,
                    )
                    discovery = None
            if not discovery:
                _LOGGER.error(
                    "Discovery codec missing or faulty for device %s with profile %s, device ignored",
                    device.name,
                    profile.device_profile.name,
                )
                continue
            for entity, config in discovery["entities"].items():
                discovery_config = config["entity_conf"]
                if not discovery_config.get("value_template"):
                    discovery_config[
                        "value_template"
                    ] = f"{{{{ value_json.object.{entity} }}}}"

            mac_version = (
                profile.device_profile.DESCRIPTOR.fields_by_name["mac_version"]
                .enum_type.values_by_number[profile.device_profile.mac_version]
                .name
            )
            mac_version = (mac_version.replace("_", " ", 1)).replace("_", ".")
            discovery["dev_conf"] = {
                "sw_version": mac_version,
                "dev_eui": device.dev_eui,
                "dev_name": device.name,
                "measurement_names": {
                    entity: profile.device_profile.measurements[entity].name
                    for entity in discovery["entities"]
                },
                "prev_value": {"batteryLevel": device.device_status.battery_level}
                if not device.device_status.external_power_source
                else {},
            }
            devices_list.append(discovery)
        return devices_list


def get_ha_descriptor(js_script):
    """Convert restricted javascript function getHaDeviceInfo code to python dictionary/array structure."""
    i_start = js_script.find("getHaDeviceInfo")
    if i_start >= 0:
        i_start = js_script.find("return", i_start)
    if i_start >= 0:
        i_start = js_script.find("{", i_start)
    if i_start < 0:
        return (None, js_script)
    open_curl = 0
    is_string = False
    is_name = False
    is_1st_slash = False
    is_comment = False
    json_out = ""
    quote = '"'
    getHaDeviceInfoSource = js_script[i_start:]
    for char in getHaDeviceInfoSource:
        if char == "\n":
            is_comment = False
            continue
        if is_comment:
            continue
        if not is_string:
            if char == "/":
                if not is_1st_slash:
                    is_1st_slash = True
                    continue
                is_1st_slash = False
                is_comment = True
                continue
            if is_1st_slash:
                is_1st_slash = False
                json_out += "/"
            if char == " ":
                continue
            if char == "{":
                open_curl += 1
                json_out += char
                json_out += '"'
                is_name = True
                continue
            if char == "}":
                open_curl -= 1
                if is_name:
                    json_out += '"'
                    is_name = False
                json_out += char
                if open_curl <= 0:
                    break
                continue
            if char == ":":
                if is_name:
                    json_out += '"'
                    is_name = False
                json_out += char
                continue
            if char == '"':
                json_out += char
                is_string = True
                quote = char
                continue
            if char == "'":
                json_out += '"'
                is_string = True
                quote = char
                continue
            if char == ",":
                json_out += char
                json_out += '"'
                is_name = True
                continue
            is_name = char != ","
            json_out += char
        elif char == quote:
            is_string = False
            json_out += '"'
        else:
            if quote != '"' and char == '"':
                json_out += "\\"
            json_out += char
    json_out = json_out.replace(',""', "")
    return (json_out, getHaDeviceInfoSource)
