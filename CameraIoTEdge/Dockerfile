FROM ellerbach/opencv:342

ADD app app

RUN apt-get update && apt-get upgrade \
    && apt-get install libboost-python-dev \
    && pip3 install azure-iothub-device-client \
    && pip3 install azure-storage-blob \
    && pip3 install flask \
    && pip3 install numpy \
    && sudo rm -rf /var/lib/apt/lists/* 

# Set the working directory
WORKDIR /app

EXPOSE 1337

# Run the flask server for the endpoints
CMD ["python3","AzurePost.py"]