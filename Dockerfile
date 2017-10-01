FROM alpine:3.6

RUN apk add --no-cache dhcp

RUN cp /etc/dhcp/dhcpd.conf.example /etc/dhcpd.conf \
    && touch /var/lib/dhcp/dhcpd.leases

ENTRYPOINT ["/usr/sbin/dhcpd", "-f"]
EXPOSE 67/udp 67/tcp 647/tcp 647/udp