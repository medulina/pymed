FROM continuumio/anaconda
RUN pip install argparse
RUN conda install -c conda-forge nibabel nipype
ADD generate_tiles.py /generate_tiles.py
RUN chmod +x /generate_tiles.py

# Use any image as your base image, or "scratch"
# Add fwatchdog binary via https://github.com/openfaas/faas/releases/
# Then set fprocess to the process you want to invoke per request - i.e. "cat" or "my_binary"

ADD https://github.com/openfaas/faas/releases/download/0.6.9/fwatchdog /usr/bin
# COPY ./fwatchdog /usr/bin/
RUN chmod +x /usr/bin/fwatchdog

# Populate example here - i.e. "cat", "sha512sum" or "node index.js"
ENV fprocess="/generate_tiles.py"

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1
CMD ["fwatchdog"]
