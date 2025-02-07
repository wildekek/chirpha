/**
 * Payload Decoder for MXI-LoRa-02
 *
 * @product Elster gas meter
 */
function decodeUplink(input) {
    var bytes = input.bytes;
    var port = input.fPort;
    var variables = input.variables;
    return jooby(bytes, variables);
}

var EVENTS={1: 'MAGNET_ON', 2:'MAGNET_OFF', 3:'ACTIVATE', 4:'DEACTIVATE', 6:'CAN_OFF', 7:'INSERT', 8:'REMOVE', 9:'COUNTER_OVER', 15:'EV_OPTOLOW', 16:'EV_OPTOFLASH'};

function jooby(bytes, variables) {
    var decoded = {};

    //console.log('Data buffer '+ bytes);
    for (var i = 0; i < bytes.length-1; ) {
        var cmd = bytes[i++];
        var cmdDataLen = bytes[i++];
        switch(cmd) {
            case 0x07:  //  GET_CURRENT - Current pulse counter value
                decoded.counter = readUInt32BE(bytes.slice(i, i + 4));
                if(variables.hasOwnProperty("counterOffset"))
                    decoded.counter+=parseInt(variables.counterOffset);
                break;
            case 0x15:  //  NEW_EVENT - New event occurs. Same as EVENTS but have different structure. EVENTS command will be not supported on new rf modules variants.
                eventType = bytes[i];
                eventName = EVENTS[eventType] || "Event"+eventType;
                eventCount = bytes[i+1];
                dateSecs = readUInt32BE(bytes.slice(i+2, i + 6)) + 946677600;
                eventTime = new Date(dateSecs * 1000);
                if(!decoded.event) {
                    decoded.event = [{name:eventName, count:eventCount, time:eventTime}];
                } else {
                    decoded.event.push({name:eventName, count:eventCount, time:eventTime});
                }
            break;
            case 0x17:  //  DATA_HOUR_DIF_MUL - Pulse counters hourly data, data accumulated on hourly basis and transmitted from jooby module on adjustable period (for multi-input rf modules)
                var ret = readExtUint(bytes, i+3);
                var hoursCount = bytes[i+2]>>>5;
                var startHour = bytes[i+2]&0x1f;
                decoded.hoursCount = hoursCount;
                decoded.startHour = startHour;
                decoded.date = new Date(DateY2000(readUInt16BE(bytes, 0)));
                var counter = 0;
                for(var iHours = 0; iHours<=hoursCount; iHours++) {
                    ret_inr = readExtUint(bytes, ret.ipos+1)
                    counter += ret_inr.num;
                    ret= ret_inr;
                }
                //  optionally using ChirpStack varaibles feature to offset resulting counter value to match meter
                if(variables.hasOwnProperty("counterOffset"))
                    counter+=parseInt(variables.counterOffset);
                decoded.counter = counter;
            break;
            case 0x09:  //  TIME2000 - Current rf module time (time 2000 format);
                decoded.time = new Date(TimeY2000(readUInt32BE(bytes, i+1)));
            break;
            case 0x14:  //  NEW_STATUS - RF Module status
                decoded.softType = bytes[i];
                decoded.softVersion = bytes[i+1];
                decoded.hardType = bytes[i+2];
                decoded.hardVersion = bytes[i+3];
                decoded.lowBattery= readUInt16BE(bytes, i+4)>>>4;
                decoded.highBattery= readUInt16BE(bytes, i+5)&0x0fff;
                decoded.resistant= readUInt16BE(bytes, i+7);
                if(bytes[i+7]<255)
                    decoded.temperature = bytes[i+9];
                decoded.batteryCapacity = Math.round(bytes[i+10]/2.55);
            break;
            case 0x20:  //  DATA_DAY - Pulse counter daily data on billing hour
            case 0x40:  //  DATA_HOUR_DIF - Pulse counter hourly data, data accumulated on hourly basis and transmitted from jooby rf module on adjustable period
            case 0x60:  //  LAST_EVENTS - Last unread event
            case 0x0C:  //  EVENTS - Critical event alarm (magnetic influence, tamper sensor, ...). Deprecated. See NEW_EVENT
            case 0x11:  //  GET_VERSION - Software version. Deprecated
            case 0x16:  //  DATA_DAY_MUL - Pulse counters daily data (for multi-input rf modules)
            case 0x18:  //  GET_CURRENT_MUL - Current pulse counters value (for multi-input rf modules)
            case 0x1E:  //  MTX_CMD - MTX 0x1e subsystem. MTX electricity meter commands
            default:
                if(!decoded.cmd) decoded.cmd = "" + cmd;
                else decoded.cmd = decoded.cmd + " " + cmd;
        }
        i+= cmdDataLen;
    }
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
    var value = (bytes[startIndex+3] << 24) + (bytes[startIndex+2] << 16) + (bytes[startIndex+1] << 8) + bytes[startIndex];
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

function readUInt32BE(bytes) {
    var value = (bytes[0] << 24) + (bytes[1] << 16) + (bytes[2] << 8) + bytes[3];
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

function DateY2000(e){
    var t=31&(e&=65535),r=15&(e>>>=5),i=2e3+(e>>>4);
    return Date.UTC(i,r-1,t,0,0,0)
}

function TimeY2000(e){
    var t,r,o=e%60,d=Math.floor(e/60)%60,hour=e/3600%24,i=(t=Math.floor(e/86400)+2451545)+(r=Math.floor((4*t-7468865)/146097))+1-Math.floor(r/4)+1524,a=Math.floor((20*i-2442)/7305),n=Math.floor(1461*a/4),s=Math.floor(1e4*(i-n)/306001);
    var c=i-n-Math.floor(306001*s/1e4),u=s<14?s-1:s-13,h=u<3?a-4715:a-4716;
    return new Date(Date.UTC(h,u-1,c,hour,d,o));
}


function getHaDeviceInfo() {
  return {
    device: {
      manufacturer: "Jooby",
      model: "MXI-LoRa-02",
    },
    entities: {
        counter:{
        entity_conf: {
          value_template: "{{ (value_json.object.counter | float) / 100 }}",
          device_class: "gas",
          state_class: "total_increasing",
          unit_of_measurement: "m³"
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
