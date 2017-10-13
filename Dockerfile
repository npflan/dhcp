FROM alpine:3.6

RUN apk add --no-cache dhcp python3 ca-certificates supervisor

RUN mkdir -p /dhcp/config/ \
    && cp /etc/dhcp/dhcpd.conf.example /dhcp/config/dhcpd.conf \
    && touch /var/lib/dhcp/dhcpd.leases

ADD supervisord.conf /etc/supervisord.conf

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY dhcpd_exporter.py .

EXPOSE 67/udp 67/tcp 647/tcp 647/udp 9405/tcp

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
