/**
 * Payload Decoder for Chirpstack v4
 *
 * Copyright 2024 Milesight IoT
 *
 * @product WS52x
 */
function decodeUplink(input) {
    var decoded = milesight(input.bytes);
    return { data: decoded };
}

function milesight(bytes) {
    var decoded = {};

    for (var i = 0; i < bytes.length; ) {
        var channel_id = bytes[i++];
        var channel_type = bytes[i++];

        // VOLTAGE
        if (channel_id === 0x03 && channel_type === 0x74) {
            decoded.voltage = readUInt16LE(bytes.slice(i, i + 2)) / 10;
            i += 2;
        }
        // ACTIVE POWER
        else if (channel_id === 0x04 && channel_type === 0x80) {
            decoded.power = readUInt32LE(bytes.slice(i, i + 4));
            i += 4;
        }
        // POWER FACTOR
        else if (channel_id === 0x05 && channel_type === 0x81) {
            decoded.factor = bytes[i];
            i += 1;
        }
        // POWER CONSUMPTION
        else if (channel_id === 0x06 && channel_type == 0x83) {
            decoded.power_sum = readUInt32LE(bytes.slice(i, i + 4));
            i += 4;
        }
        // CURRENT
        else if (channel_id === 0x07 && channel_type == 0xc9) {
            decoded.current = readUInt16LE(bytes.slice(i, i + 2));
            i += 2;
        }
        // STATE
        else if (channel_id === 0x08 && channel_type == 0x70) {
            decoded.state = bytes[i] == 1 || bytes[i] == 0x11 ? "open" : "close";
            i += 1;
        } else if (channel_id === 0xff && channel_type == 0x3f) {
            decoded.outage = bytes[i] == 0xff ? "OFF" : "ON";
            i += 1;
        } else {
            break;
        }
    }
	if(!decoded.hasOwnProperty('outage')) decoded.outage = "ON";
    return decoded;
}

/* ******************************************
 * bytes to number
 ********************************************/
function readUInt16LE(bytes) {
    var value = (bytes[1] << 8) + bytes[0];
    return value & 0xffff;
}

function readUInt32LE(bytes) {
    var value = (bytes[3] << 24) + (bytes[2] << 16) + (bytes[1] << 8) + bytes[0];
    return (value & 0xffffffff) >>> 0;
}

function encodeDownlink(input) {
  var bytes = [];
  if(input.object.hasOwnProperty("switch")) {
    if(input.object.switch=="open") bytes.push(0x08, 0x00,0x00,0xff);
    if(input.object.switch=="close") bytes.push(0x08, 0x01,0x00,0xff);
  }
  return {bytes: bytes};
}

function getHaDeviceInfo() {
  return {
    device: {
      manufacturer: "Milesight IoT Co., Ltd",
      model: "WS52x"
    },
    entities: {
        current:{
        entity_conf: {
          value_template: "{{ (value_json.object.current | float) / 1000 }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "current",
          unit_of_measurement: "A"
        }
      },
        factor:{
        entity_conf: {
          value_template: "{{ (value_json.object.factor | float) / 100 }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "power_factor",
        }
      },
      power:{
        entity_conf: {
          value_template: "{{ value_json.object.power | float }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "power",
          unit_of_measurement: "W"
        }
      },
      voltage:{
        entity_conf: {
          value_template: "{{ value_json.object.voltage | float }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "voltage",
          unit_of_measurement: "V"
        }
      },
      outage:{
        integration: "binary_sensor",
        entity_conf: {
          entity_category: "diagnostic",
          device_class: "power"
        }
      },
      power_sum:{
        entity_conf: {
          value_template: "{{ (value_json.object.power_sum | float) / 1000 }}",
          state_class: "total_increasing",
          device_class: "energy",
          unit_of_measurement: "kWh"
        }
      },
      state:{
       integration: "switch",
       entity_conf: {
          value_template: "{{ value_json.object.state }}",
          command_topic: "{command_topic}",
          state_on: "open",
          state_off: "close",
          payload_off: '{"devEui":"{dev_eui}","confirmed":true,"fPort":85,"data":"CAAA/w=="}',
          payload_on: '{"devEui":"{dev_eui}","confirmed":true,"fPort":85,"data":"CAEA/w=="}'
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
