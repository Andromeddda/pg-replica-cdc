FROM postgres:16

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER postgres

ENTRYPOINT ["/entrypoint.sh"]