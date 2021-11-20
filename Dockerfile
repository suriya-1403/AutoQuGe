FROM python:3.9.7
ADD . /AUTOQUGE
WORKDIR /AUTOQUGE
RUN pip install -r requirements.txt