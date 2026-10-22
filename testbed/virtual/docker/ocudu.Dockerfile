FROM ubuntu:24.04 AS dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build pkg-config git ca-certificates \
    libfftw3-dev libmbedtls-dev libsctp-dev libyaml-cpp-dev libzmq3-dev \
    libgtest-dev iproute2 iputils-ping && rm -rf /var/lib/apt/lists/*

FROM dependencies AS builder
COPY sources/ocudu /src
ARG BUILD_JOBS=2
# Git on Windows can check out these upstream symlinks as target-path files.
RUN for link in /src/cmake/modules/FindBackward.cmake /src/LICENSES/BSD-3-Clause-Open-MPI.txt; do \
      if [ ! -L "$link" ]; then target=$(tr -d '\r\n' < "$link"); ln -sf "$target" "$link"; fi; \
    done \
    && cmake -S /src -B /build -G Ninja \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=OFF \
    -DENABLE_EXPORT=ON -DENABLE_ZEROMQ=ON -DENABLE_UHD=OFF \
    -DENABLE_DPDK=OFF -DENABLE_WERROR=OFF -DMARCH=x86-64-v3 \
    && cmake --build /build --target ocu odu --parallel ${BUILD_JOBS}

FROM dependencies
COPY --from=builder /build/apps/cu/ocu /usr/local/bin/ocu
COPY --from=builder /build/apps/du/odu /usr/local/bin/odu
CMD ["ocu", "--help"]
