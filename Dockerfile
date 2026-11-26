# syntax=docker/dockerfile:1
FROM ubuntu:noble-20261110.1@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git python3 build-essential jq zstd xz-utils && \
    rm -rf /var/lib/apt/lists/* && useradd --create-home reproducer
USER reproducer
WORKDIR /home/reproducer/review
ENV ELAN_HOME=/home/reproducer/.elan
ENV PATH=/home/reproducer/.elan/bin:$PATH
COPY --chown=reproducer:reproducer primary/ primary/
COPY --chown=reproducer:reproducer checks/ checks/
COPY --chown=reproducer:reproducer reproduce/ reproduce/
COPY --chown=reproducer:reproducer source-lock.json source-lock.json
WORKDIR /home/reproducer/review/primary/vp-vnp
RUN curl -fLsS --proto '=https' -o /tmp/elan.tar.gz \
      https://github.com/leanprover/elan/releases/download/v4.2.3/elan-x86_64-unknown-linux-gnu.tar.gz && \
    echo 'df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2  /tmp/elan.tar.gz' | sha256sum -c - && \
    tar -xzf /tmp/elan.tar.gz -C /tmp && /tmp/elan-init -y --no-modify-path --default-toolchain none && \
    rm /tmp/elan.tar.gz /tmp/elan-init && lean --version && lake exe cache get && \
    python3 ../../reproduce/verify_tier2.py --inputs-only

FROM base AS tier1
CMD ["bash", "../../reproduce/in-container.sh", "1"]

FROM base AS tier2
RUN mkdir -p /home/reproducer/toolchains && \
    curl -fLsS --proto '=https' -o /tmp/go.tar.gz https://dl.google.com/go/go1.25.5.linux-amd64.tar.gz && \
    echo '9e9b755d63b36acf30c12a9a3fc379243714c1c6d3dd72861da637f336ebb35b  /tmp/go.tar.gz' | sha256sum -c - && \
    tar -xzf /tmp/go.tar.gz -C /home/reproducer/toolchains && rm /tmp/go.tar.gz && \
    curl -fLsS --proto '=https' -o /tmp/rust.tar.xz https://static.rust-lang.org/dist/rust-1.91.1-x86_64-unknown-linux-gnu.tar.xz && \
    echo 'db178028da493a663b2e344a142076fb0f72adea4120043983f488de9cf95214  /tmp/rust.tar.xz' | sha256sum -c - && \
    tar -xJf /tmp/rust.tar.xz -C /tmp && \
    /tmp/rust-1.91.1-x86_64-unknown-linux-gnu/install.sh --prefix=/home/reproducer/toolchains/rust \
      --components=rustc,cargo,rust-std-x86_64-unknown-linux-gnu --disable-ldconfig && \
    rm -r /tmp/rust.tar.xz /tmp/rust-1.91.1-x86_64-unknown-linux-gnu
ENV PATH=/home/reproducer/toolchains/go/bin:/home/reproducer/toolchains/rust/bin:$PATH
ENV TOOLS_DIR=/home/reproducer/verifiers
RUN bash ../../reproduce/build-verifiers.sh
CMD ["bash", "../../reproduce/in-container.sh", "2"]
