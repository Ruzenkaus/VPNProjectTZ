FROM python:3.9

WORKDIR /VPNProjectTZ

COPY requirements.txt .

RUN pip3 install -r requirements.txt

ADD main.py .
ADD check_proxies.py .
COPY templates /VPNProjectTZ/templates
COPY instance /VPNProjectTZ/instance
COPY valid_proxies /VPNProjectTZ/valid_proxies

CMD ["python", "./main.py"]