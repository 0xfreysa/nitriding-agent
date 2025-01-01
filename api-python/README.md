Agent example
=================

This directory conatains an api allowing to call an agent
[Python script](service.py)
api server, interacts with nitriding service to generate the attestation.
[Dockerfile](Dockerfile) adds the nitriding standalone executable along with the
enclave application, consisting of the
[shell script](start.sh)
that invokes nitriding in the background, followed by running the Python script.
[shell script](gvproxy.sh)
Runs gvproxy, whichs forward the HTTP request to the enclave.

To build the nitriding executable, the Docker image, the enclave image, and
finally run the enclave image, simply run:

    make
    ./gvproxy.sh
