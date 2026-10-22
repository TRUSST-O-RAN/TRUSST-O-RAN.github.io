# This prefix matches the portable builder so Docker can reuse its compile cache.
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

FROM builder AS instrumented
COPY instrumentation/ocudu.patch instrumentation/source-files.sha256 instrumentation/trusst_lab.h /overlay/
RUN cd /src \
 && cut -c67- /overlay/source-files.sha256 | xargs sed -i 's/\r$//' \
 && sha256sum -c /overlay/source-files.sha256 \
 && git apply --check /overlay/ocudu.patch \
 && git apply /overlay/ocudu.patch \
 && cp /overlay/trusst_lab.h /src/include/ocudu/support/trusst_lab.h \
 && cmake --build /build --target ocu odu --parallel ${BUILD_JOBS}

FROM dependencies
COPY --from=instrumented /build/apps/cu/ocu /usr/local/bin/ocu
COPY --from=instrumented /build/apps/du/odu /usr/local/bin/odu
COPY instrumentation/ocudu.patch instrumentation/source-files.sha256 instrumentation/trusst_lab.h /usr/local/share/trusst-instrumentation/
ARG INSTRUMENTATION_SHA256
LABEL org.trusst.ocudu.commit="a785384da53b325174142ff503dbd4d222b233d0" \
      org.trusst.instrumentation.schema="trusst.f1-state.v1" \
      org.trusst.instrumentation.sha256="${INSTRUMENTATION_SHA256}"
CMD ["ocu", "--help"]
