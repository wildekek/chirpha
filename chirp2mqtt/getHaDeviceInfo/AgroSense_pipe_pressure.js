/**
 * Payload Decoder for     AgroSense Pipe Pressure Sensor
 *
 * @product Pipe Pressure Sensor
 */
function decodeUplink(input) {
  var bytes = input.bytes;
  var port = input.fPort;
  var variables = input.variables;
  return agrosense(bytes, variables);
}

function agrosense(bytes, variables) {
  var decoded = {};

  decoded.sequence = readUInt16BE(bytes, 0);
  decoded.battery_voltage = bytes[2] * 0.1;
  decoded.adc = readUInt16BE(bytes, 3) * 0.001;
  if(variables.hasOwnProperty("offset")) offset=variables.offset; else offset=-0.483;
  if(variables.hasOwnProperty("gradient")) gradient=variables.gradient; else gradient=250;
  decoded.pressure = (decoded.adc+offset)*gradient
  decoded.pressure = Math.round(decoded.pressure * 1000) / 1000;
  decoded.time_interval = readUInt32BE(bytes, 13) / 1000 / 60;
  decoded.data_valid = bytes[17]==1;

  return {data: decoded};
}

/* ******************************************
 * bytes to number
 ********************************************/
function readUInt16LE(bytes) {
  var value = (bytes[1] << 8) + bytes[0];
  return value & 0xffff;
}

function readUInt16BE(bytes, startIndex) {
  var value = (bytes[startIndex] << 8) + bytes[startIndex+1];
  return value & 0xffff;
}

function readUInt32BE(bytes, startIndex) {
  var value = (bytes[startIndex+0] << 24) + (bytes[startIndex+1] << 16) + (bytes[startIndex+2] << 8) + bytes[startIndex+3];
  return value & 0xffffffff;
}

function readInt16LE(bytes) {
  var ref = readUInt16LE(bytes);
  return ref > 0x7fff ? ref - 0x10000 : ref;
}

function readUInt32LE(bytes) {
  var value = (bytes[3] << 24) + (bytes[2] << 16) + (bytes[1] << 8) + bytes[0];
  return value & 0xffffffff;
}

function readExtUint(bytes, startPos){
  var ret_val = {};
  for(var t=0,r=startPos;r<bytes.length;r++){
      var i=bytes[r];
      ret_val.ipos= r;
      if(t|=(127&i)<<7*(r-startPos),0==(128&i)) break;
  }
  ret_val.num = t;
  return ret_val;
}

// Encoder function to be used in the TTN console for downlink payload（Fport 1）
function encodeDownlink(input) {
  var seconds = input.data.minutes * 60 * 1000; //minutes * 60;
//throw new Error("Reload time: " + JSON.stringify(input) + "+++++++");


  var payload = [
      (seconds >> 24) & 0xFF,
      (seconds >> 16) & 0xFF,
      (seconds >> 8) & 0xFF,
      seconds & 0xFF
  ];

  return { bytes: payload };
}

function getHaDeviceInfo() {
return {
  device: {
    manufacturer: "Makerfab",
    model: "AgroSense Pipe Pressure Sensor",
  },
  entities: {
      battery_voltage:{
      entity_conf: {
        value_template: "{{ value_json.object.battery_voltage | float }}",
        entity_category: "diagnostic",
        device_class: "voltage",
        unit_of_measurement: "V"
      }
    },
    adc:{
      entity_conf: {
        value_template: "{{ value_json.object.adc | float }}",
        device_class: "voltage",
        unit_of_measurement: "V",
      }
    },
    pressure:{
      entity_conf: {
        value_template: "{{ value_json.object.pressure | float }}",
        device_class: "pressure",
        unit_of_measurement: "kPa",
      }
    },
    time_interval:{
      integration: "number",
      entity_conf: {
         value_template: "{{ value_json.object.time_interval | int }}",
         unit_of_measurement: "min",
         command_topic: "{command_topic}",
         command_template: '{"devEui":"{dev_eui}","confirmed":true,"fPort":1,"object":{ "minutes":{{ value }}}}',
         min: 5,
         max: 1440
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
