"""The Chirpstack LoRaWan integration - setup."""
from __future__ import annotations
__version__ = "1.1.46"

import logging
import logging.handlers
import json
import signal
import os
from pathlib import Path
from typing import Final

from .grpc import ChirpGrpc
from .mqtt import ChirpToHA
from .const import CONF_APPLICATION_ID

# Date/Time formats
FORMAT_DATE: Final = "%Y-%m-%d"
FORMAT_TIME: Final = "%H:%M:%S"
FORMAT_DATETIME: Final = f"{FORMAT_DATE} {FORMAT_TIME}"
FMT = ( "%(asctime)s.%(msecs)03d chirpha %(levelname)s [%(name)s] %(message)s" )
CONFIGURATION_FILE = '/data/options.json'

_LOGGER = logging.getLogger(__name__)

INTERNAL_CONFIG = {
  "chirpstack_api_server": "localhost",
  "server_port": 8080,
  "mqtt_server": "core-mosquitto",
  "mqtt_port": 1883,
}

class run_chirp_ha:
    def __init__(self) -> None:
        self._grpc_client = None
        self._mqtt_client = None
        self._config = None
        signal.signal(signal.SIGTERM, self.stop_chirp_ha)
        pass

    def stop_chirp_ha(self, signum, frame):
        _LOGGER.info("Shutdown requested")
        if self._mqtt_client:   # close to exit server loop
            _LOGGER.info("Closing MQTT connection")
            self._mqtt_client.close()
            self._mqtt_client = None

    def main(self):
        logging.basicConfig(level=logging.INFO, format=FMT, datefmt=FORMAT_DATETIME) #, handlers=[logging.handlers.SysLogHandler()])
        config = None
        try:
            module_dir = Path(globals().get("__file__", "./_")).absolute().parent
            _LOGGER.info("Chirp started %s, %s", os.getcwd(), module_dir)
            with open(CONFIGURATION_FILE, 'r') as file:
                config = json.load(file)
            config = config | INTERNAL_CONFIG
            self._config = config
            with open(str(module_dir)+'/classes.json', 'r') as file:
                classes = json.load(file)
            log_level = logging._nameToLevel.get(config['log_level'].upper(),logging.INFO)
            log_level = logging.DEBUG
            logging.basicConfig(level=log_level, format=FMT, datefmt=FORMAT_DATETIME)
            _LOGGER.info("Version %s", __version__)
            self._grpc_client = ChirpGrpc(config, __version__)
            self._mqtt_client = ChirpToHA(config, __version__, classes, self._grpc_client)

            #self._mqtt_client.start_bridge()

            self._mqtt_client._client.loop_forever()
        except Exception as error:
            _LOGGER.exception("Chirp failed: %s", str(error))
        finally:
            if self._mqtt_client:
                _LOGGER.info("Closing MQTT connection")
                self._mqtt_client.close()
                self._mqtt_client = None
            if self._grpc_client:
                _LOGGER.info("Closing gRPC connection")
                self._grpc_client.close()
                if self._config[CONF_APPLICATION_ID] != self._grpc_client._application_id and False:
                    self._config[CONF_APPLICATION_ID] = self._grpc_client._application_id
                    with open(CONFIGURATION_FILE, 'w') as file:
                        json.dump(self._config, file)
                self._grpc_client = None


if __name__=='__main__':
    run_chirp_ha().main()
    _LOGGER.info("Done.")
