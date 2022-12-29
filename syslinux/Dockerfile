FROM debian:10 AS buildtime
COPY container-script.sh /root/build.sh
RUN mkdir /root/destdir/ && cd /root/destdir/ && chmod +x ../build.sh && ../build.sh
RUN cd /root/ && tar cvzf destdir.tgz ./destdir/
CMD cp -v /root/destdir.tgz /host/ && ls /host/
