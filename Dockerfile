FROM golang:1.22-alpine3.18 as build

RUN apk add --no-cache \
  unzip

RUN mkdir -p /app/bin
# install Tesla Go packages
ADD https://github.com/teslamotors/vehicle-command/archive/refs/heads/main.zip /tmp
RUN unzip /tmp/main.zip -d /app
WORKDIR /app/vehicle-command-main
RUN go get ./...
RUN go build -o /app/bin ./...

FROM alpine:3.19.1

# install dependencies
RUN apk add --no-cache \
  python3 \
  py3-flask \
  py3-requests

# Create various working directories
RUN mkdir /config

# Copy project files into required locations
COPY tesla_http_proxy/app /app

# Copy tesla-http-proxy binary from build stage
COPY --from=build /app/bin/tesla-http-proxy /app/bin/tesla-keygen /usr/bin/

# Set environment variables
ENV CONFIG_BASE="/config"

WORKDIR /app
ENTRYPOINT ["/app/run.sh"]
