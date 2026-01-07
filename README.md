# Nevodchik

![license](https://img.shields.io/badge/Apache--2.0-green?logo=apache&style=plastic)
![prog_lang](https://img.shields.io/badge/Python-blue?logo=python&logoColor=darkgray&style=plastic)
![calver](https://img.shields.io/badge/calver-YYYY.0M--PATCH-22bfda?style=plastic)

The bot for LoRa mesh networks.

### What a strange name...

**Nevodchic** - from the old colloquial Russian word "не́водчик": a fisherman who catches fish with a seine ("невод").
So, a mesh, a seine. Both are latticed. Get it? Me neither...

### What is it for?

This application allows you to connect to an MQTT broker, format received packets with user messages in human-readable format, and send them to IRC and/or a connected Telegram bot.
The project is aimed at working with LoRa mesh networks. Currently, it is targeting Meshtastic.

Build and run
-------------

If you already have Podman installed, you can use `run-podman.sh` for a quick start, but it is not a production-ready variant. This script has a help-menu, so just type `./run-podman.sh help` to see it.

Also if you are familiar with `uv` then you can run the app on the host as is. Later I'll provide a step-by-step guide to do this, but for now I assume that the reader knows about `uv build`, `uv sync` and *virutal environments*. After setting up an environment, run scripts `dload-protobufs.sh` and `build-protobufs.sh`: this is the essential thing to do, we need those generated protobufs to decode LoRa messages! Only after this step you are able to *build* and *run* the app.

Configuration
-------------

All configs are in TOML format and are located in the following directory by default: `./config/`. Accordingly, in the container this directory is located as follows: `/nevodchik/config/`, so you can use volume-mount directives to attach external directory with configs of yours. I hope that those configs are easy to understand and are self-explanatory, so there is no need to provide a full documentation (*lazybones detected*).

Values ​​from main configuration files can be overridden by environment variables.

First things first, setup the internal MQTT-client: specify the connection parameters to your server! So either edit `nevodchik.conf` or pass env-vars (replace with your values, ofc):
* MQTT_HOST="localhost"
* MQTT_PORT=1883
* MQTT_USER="user"
* MQTT_PASSW="pass"

Current state
-------------

- [x] Containerized (Podman-targeted)
- [x] TOML configs
- [x] Able to connect to a MQTT-server
- [x] Primitive parsing of the topic
- [x] Decrypts and decodes Meshtastic® text messages (on the default channel)
- [ ] Telegram-bot integration
- [ ] IRC-bot integration
- [ ] Collecting and analyzing data

*Stay tuned...*

License
-------

Nevodchik is licensed under the Apache-2.0 license. See LICENSE for details.