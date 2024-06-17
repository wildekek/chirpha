ARG BUILD_FROM
# amd64: alpine:${VERSION}
# i386: i386/alpine:${VERSION}
# aarch64: arm64v8/alpine:${VERSION}
# armv7: arm32v7/alpine:${VERSION}
# armhf: arm32v6/alpine:${VERSION}

FROM ${BUILD_FROM}

ENV \
    PGDATA="/data/postgres"

# Set shell
SHELL ["/bin/ash", "-o", "pipefail", "-c"]

ARG CHIRPSTACK_VERSION
ARG CHIRPSTACK_GATEWAY_BRIDGE_VERSION
ARG BUILD_ARCH

WORKDIR /usr/local/bin

RUN \
    apk --no-cache add python3 \
    && apk --no-cache add py3-pip \
#    && apk del grpcio \
#
#    && pip3 install grpcio==1.64.1 \
    && pip3 install chirpstack-api==4.7.0 paho-mqtt --break-system-packages \
#    && pip3 install chirpstack-api paho-mqtt --break-system-packages \
    && apk --no-cache add git redis postgresql postgresql-contrib su-exec \
    && sed -i 's/protected-mode yes/protected-mode no/' /etc/redis.conf \
    && sed -i 's/^\(bind .*\)$/# \1/' /etc/redis.conf \
    && sed -i 's/^\(daemonize .*\)$/# \1/' /etc/redis.conf \
    && sed -i 's/^\(dir .*\)$/# \1\ndir \/data\/redis/' /etc/redis.conf \
    && sed -i 's/^\(logfile .*\)$/# \1/' /etc/redis.conf \
    && sed -i 's/loglevel notice/loglevel warning/' /etc/redis.conf \
    && mkdir -p "$PGDATA" && chown -R postgres:postgres "$PGDATA" && chmod 1777 "$PGDATA" \
    && if [[ "$BUILD_ARCH" = "amd64" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack/chirpstack_${CHIRPSTACK_VERSION}_linux_amd64.tar.gz -O - | tar -xz;  fi \
    && if [[ "$BUILD_ARCH" = "amd64" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack-gateway-bridge/chirpstack-gateway-bridge_${CHIRPSTACK_GATEWAY_BRIDGE_VERSION}_linux_amd64.tar.gz -O - | tar -xz;  fi \
    && if [[ "$BUILD_ARCH" = "aarch64" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack/chirpstack_${CHIRPSTACK_VERSION}_linux_arm64.tar.gz -O - | tar -xz; fi \
    && if [[ "$BUILD_ARCH" = "aarch64" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack-gateway-bridge/chirpstack-gateway-bridge_${CHIRPSTACK_GATEWAY_BRIDGE_VERSION}_linux_arm64.tar.gz -O - | tar -xz; fi \
    && if [[ "$BUILD_ARCH" = "armhf" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack/chirpstack_${CHIRPSTACK_VERSION}_linux_armv7hf.tar.gz -O - | tar -xz; fi \
    && if [[ "$BUILD_ARCH" = "armhf" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack-gateway-bridge/chirpstack-gateway-bridge_${CHIRPSTACK_GATEWAY_BRIDGE_VERSION}_linux_armv7hf.tar.gz -O - | tar -xz; fi \
    && if [[ "$BUILD_ARCH" = "armv7" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack/chirpstack_${CHIRPSTACK_VERSION}_linux_armv7hf.tar.gz -O - | tar -xz; fi \
    && if [[ "$BUILD_ARCH" = "armv7" ]]; then wget -c https://artifacts.chirpstack.io/downloads/chirpstack-gateway-bridge/chirpstack-gateway-bridge_${CHIRPSTACK_GATEWAY_BRIDGE_VERSION}_linux_armv7hf.tar.gz -O - | tar -xz; fi

# Build arugments
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_VERSION
ARG BUILD_REPOSITORY

# Labels
LABEL \
    io.hass.version=${BUILD_VERSION} \
    io.hass.type="addon" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.name="Addon Chirp2MQTT for ${BUILD_ARCH}" \
    io.hass.description="Home Assistant Community Add-on: ${BUILD_ARCH} Chirp2MQTT image" \
#    maintainer="Franck Nijhof <frenck@addons.community>" \
#    org.opencontainers.image.title="Addon Python base for ${BUILD_ARCH}" \
#    org.opencontainers.image.description="Home Assistant Community Add-on: ${BUILD_ARCH} Python base image" \
#    org.opencontainers.image.vendor="Home Assistant Community Add-ons" \
#    org.opencontainers.image.authors="Franck Nijhof <frenck@addons.community>" \
    org.opencontainers.image.licenses="MIT" \
#    org.opencontainers.image.url="https://addons.community" \
#    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
#    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/master/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}

EXPOSE 8080
#EXPOSE 8099
EXPOSE 1700/udp

# Root filesystem
COPY rootfs /

# S6-Overlay
WORKDIR /
ENTRYPOINT ["/init"]
