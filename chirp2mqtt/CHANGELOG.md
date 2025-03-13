<!-- https://developers.home-assistant.io/docs/add-ons/presentation#keeping-a-changelog -->

## 1.1.136

- Code synchronization with chirp integration .
- Log level reduced to warnings for ChirpStack gateway .

## 1.1.135

- Added device eui specific parameter support via getHaDeviceInfo .

## 1.1.134

- Added option to import device templates from git repository.

## 1.1.132

- HA MQTT integration component device name processing change - getHaDeviceInfo data now has highest priority, the same for entities and 'enabled_by_default'.

## 1.1.131

- ChirpStack secret to configuration parameters
- HA MQTT integration component name processing change - getHaDeviceInfo data now has highest priority

## 1.1.128

- Added LORA region selection to configuratiom, fixed missinging MQTT user/password propagation to ChirpStack components (defaults were used always)

## 1.1.127

- Added optional expire after MQTT configuration item discovery message

## 1.1.126

- Added logging control via MQTT message: topic application/{ChirpStack appId}/bridge/info, message '{"log_level":"debug"}'. Added per device online checks. Initialization and logging re-factoring

## 1.1.125

- Tests extension and minor fixes in code, file cleanup. Initialization re-factoring, fixed issue with log level

## 1.1.116

- Code extended to support MQTT component integrations. Replaced custom js evaluator with dukpy package

## 1.1.108

- Added MQTT server naming requirements to documentation. Added payload checks. Fixed MQTT server IP naming in region description file. Upgrade to ghcr.io/hassio-addons/base:17.1.0, CHIRPSTACK_VERSION: 4.11.0

## 1.1.102

- Initial release
