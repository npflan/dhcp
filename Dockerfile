FROM alpine:3.6

RUN apk update
RUN apk add --no-cache dhcp python3 py-pip ca-certificates

RUN pip install supervisor

RUN cp /etc/dhcp/dhcpd.conf.example /etc/dhcpd.conf \
    && touch /var/lib/dhcp/dhcpd.leases

ADD supervisord.conf /etc/supervisord.conf

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY dhcpd_exporter.py .

EXPOSE 67/udp 67/tcp 647/tcp 647/udp 9405/tcp 9405/udp

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
