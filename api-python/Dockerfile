# A Go base image is enough to build nitriding reproducibly.
# We use a specific instead of the latest image to ensure reproducibility.
FROM golang:1.22 as builder

WORKDIR /    

# Clone the repository and build the stand-alone nitriding executable.
RUN git clone https://github.com/brave/nitriding-daemon.git
ARG TARGETARCH
RUN ARCH=${TARGETARCH} make -C nitriding-daemon/ nitriding

# Use the intermediate builder image to add our files.  This is necessary to
# avoid intermediate layers that contain inconsistent file permissions.
COPY service.py start.sh sign_tx.py /bin/
RUN chown root:root /bin/service.py /bin/start.sh
RUN chmod 0755      /bin/service.py /bin/start.sh

FROM python:3.12-slim-bullseye
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pnpm

RUN pip install flask anthropic ecdsa eth-hash[pycryptodome] eth_account web3

# Copy all our files to the final image.
COPY --from=builder /nitriding-daemon/nitriding /bin/start.sh /bin/service.py /bin/sign_tx.py /bin/

RUN git clone https://github.com/0xfreysa/nft-module /bin/freysa-autonomous-project
RUN rm -rf .git
RUN cd /bin/freysa-autonomous-project && pnpm install

CMD ["start.sh"]
