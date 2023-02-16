FROM clamsproject/clams-python-opencv4
# general
RUN apt-get update && apt-get install -y build-essential cmake \
    wget git unzip

# lib for tesseract
RUN apt-get -y install \
        g++ \
        autoconf \
        automake \
        libtool \
        autoconf-archive \
        zlib1g-dev \
        libicu-dev \
        libpango1.0-dev \
        libcairo2-dev

# tesseract 4
RUN apt-get install -y libleptonica-dev \
    libtesseract4 \
    libtesseract-dev \
    tesseract-ocr

# Get language data.
RUN apt-get install -y \
    tesseract-ocr-eng
    # add more if needed

#RUN apt-get -y clean all && \
#    rm -rf /var/lib/apt/lists/* && \
#
#    # Clean
#    apt-get -y remove \
#        python3-dev \
#        libatlas-base-dev \
#        gfortran \
#        libgtk2.0-dev \
#        libavcodec-dev \
#        libavformat-dev \
#        libswscale-dev \
#        libjpeg-dev \
#        libpng-dev \
#        libtiff-dev \
#        libv4l-dev
#        && \
#    apt-get clean && \
#    rm -rf /opencv /opencv_contrib /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./ ./app
WORKDIR /app

ENTRYPOINT ["python3"]
CMD ["app.py"]