FROM --platform=$BUILDPLATFORM golang:1.20-alpine AS builder

RUN apk update && apk add --no-cache git

WORKDIR /usr/src/app

COPY intake ./intake
COPY common ./common
COPY go.work .
COPY go.work.sum .

RUN ls

ENV GOOS=${TARGETOS}
ENV GOARCH=${TARGETARCH}
RUN go build -o /go/bin/intake github.com/luctowers/lurien/intake

FROM scratch

COPY --from=builder /go/bin/intake /go/bin/intake

ENTRYPOINT ["/go/bin/intake"]
