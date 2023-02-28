FROM --platform=$BUILDPLATFORM golang:1.20-alpine AS builder

RUN apk update && apk add --no-cache git ca-certificates && update-ca-certificates

RUN adduser -D -u 10001 appuser

WORKDIR /usr/src/app

COPY intake/go.mod intake/go.sum ./
RUN go mod download
COPY common/go.mod common/go.sum ./
RUN go mod download
RUN rm go.mod go.sum

COPY intake ./intake
COPY common ./common
COPY go.work go.work.sum ./

ENV GOOS=${TARGETOS}
ENV GOARCH=${TARGETARCH}
RUN go build -ldflags="-w -s" -o /go/bin/intake github.com/luctowers/lurien/intake

FROM scratch

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /go/bin/intake /go/bin/intake
COPY --from=builder /etc/passwd /etc/passwd
USER appuser

ENTRYPOINT ["/go/bin/intake"]
