function getHaDeviceInfo() {
    return {
      device: {
        manufacturer: "Milesight IoT Co., Ltd",
        model: "EM300-TH",
      },
      entities: {
        humidity:{
          entity_conf: {
            value_template: "{{ value_json.object.humidity | float }}",
            device_class: "humidity",
            unit_of_measurement: "%"
          }
        },
        temperature:{
          entity_conf: {
            value_template: "{{ value_json.object.temperature | float }}",
            device_class: "temperature",
            unit_of_measurement: "°C"
          }
        },
        magnet_status:{
          entity_conf: {
            value_template: "{{ value_json.object.magnet_status }}",
            device_class: "door",
          }
        },
        battery:{
          data_event: "status",
          entity_conf: {
            value_template: "{{ value_json.batteryLevel | int }}",
            entity_category: "diagnostic",
            device_class: "battery",
            unit_of_measurement: "%",
          }
        },
        rssi:{
          entity_conf: {
            value_template: "{{ value_json.rxInfo[-1].rssi | int }}",
            entity_category: "diagnostic",
            device_class: "signal_strength",
            unit_of_measurement: "dBm",
          }
        }
      }
    };
  }
