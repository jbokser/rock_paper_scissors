
FROM ubuntu:18.04

RUN apt-get update && apt-get install -y python3 python3-pip

COPY shell.json /opt
COPY shell.py /opt
COPY requirements.txt /opt

RUN pip3 install -r /opt/requirements.txt
RUN rm -f /opt/requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

CMD /opt/shell.py
