FROM ubuntu:22.04 AS dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build pkg-config libfftw3-dev \
    libmbedtls-dev libboost-program-options-dev libconfig++-dev \
    libsctp-dev libzmq3-dev iproute2 iputils-ping ca-certificates \
    && rm -rf /var/lib/apt/lists/*

FROM dependencies AS builder
COPY sources/srsran4g /src
ARG BUILD_JOBS=2
RUN cmake -S /src -B /build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_ZEROMQ=ON \
    -DENABLE_UHD=OFF -DENABLE_SOAPYSDR=OFF -DENABLE_BLADERF=OFF \
    -DENABLE_SRSENB=OFF -DENABLE_SRSEPC=OFF -DBUILD_TESTING=OFF \
    -DENABLE_RF_PLUGINS=OFF -DENABLE_GUI=OFF -DENABLE_WERROR=OFF \
    && cmake --build /build --target srsue --parallel ${BUILD_JOBS}

FROM dependencies
COPY --from=builder /build/srsue/src/srsue /usr/local/bin/srsue
CMD ["srsue", "--help"]
