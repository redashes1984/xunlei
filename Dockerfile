FROM --platform=${TARGETARCH} python:3.12-slim
ARG TARGETARCH

LABEL org.opencontainers.image.authors="redashes" \
  org.opencontainers.image.source="https://github.com/redashes1984/xunlei" \
  org.opencontainers.image.description="Thunder remote download + xlmcp headless bridge (REST API / CLI / MCP)" \
  org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install --no-install-recommends -y ca-certificates tzdata \
  && rm -rf /var/lib/apt/lists/* \
  && rm -f /etc/localtime \
  && cp -Lr /usr/share/zoneinfo/Asia/Chongqing /etc/localtime \
  && echo "Asia/Chongqing" > /etc/timezone

# panel binary (static, CGO_ENABLED=0) + xlmcp sidecar + supervisor entrypoint
# chroot root is /xunlei — pre-seed it with the loader + libc so the
# extracted xunlei-pan-cli launcher can exec inside the chroot.
RUN mkdir -p /xunlei/lib /xunlei/lib64 /xunlei/usr && \
  cp -aL /lib/. /xunlei/lib/ && \
  if [ -d /lib64 ]; then cp -aL /lib64/. /xunlei/lib64/; fi && \
  cp -a /usr/lib/. /xunlei/usr/lib/ && \
  mkdir -p /xunlei/etc/ssl/certs && \
  cp -L /etc/ssl/certs/ca-certificates.crt /xunlei/etc/ssl/certs/

COPY artifacts/xlp-${TARGETARCH} /xlp
COPY xlmcp.py /xlmcp.py
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /xlp /docker-entrypoint.sh

# panel env (names identical to cnk3x/xunlei upstream)
ENV XL_DASHBOARD_PORT=2345 \
  XL_DASHBOARD_IP= \
  XL_DASHBOARD_USERNAME= \
  XL_DIR_DOWNLOAD=/xunlei/downloads \
  XL_PREVENT_UPDATE= \
  XL_UID= \
  XL_GID= \
  XL_DEBUG= \
  XL_SPK_URL= \
# xlmcp sidecar env
  XL_HOST=127.0.0.1 \
  XL_PORT=2345 \
  XL_API_PORT=8787

VOLUME [ "/xunlei/data", "/xunlei/downloads" ]
EXPOSE 2345 8787

ENTRYPOINT [ "/docker-entrypoint.sh" ]
