package main

import (
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"time"

	v4 "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
	"github.com/luctowers/lurien/common"
	"go.uber.org/zap"
)

func Metadata() common.Handler {
	return &metadataHandler{}
}

type metadataHandler struct{}

func (h *metadataHandler) Handle(i common.Input) (int, error) {
	i.Response.Header().Set("Content-Type", "application/json")
	i.Response.Write([]byte(`{
		"games": {
			"hollowknight": {
				"maximumSaveSize": 400000,
				"includeSaves": [

				],
				"excludeSaves": [

				]
			},
			"silksong": {
				"maximumSaveSize": 10000000,
				"includeSaves": [

				],
				"excludeSaves": [
					
				]
			}
		}
	}`))
	return http.StatusOK, nil
}

func Intake(s3c *s3.Client, s3bucket string) common.Handler {
	return &intakeHandler{
		s3c:      s3c,
		s3bucket: s3bucket,
		// save format: name---ts.ext
		saveExpr: regexp.MustCompile(`(.*)---([0-9]{4}-[0-9]{2}-[0-9]{2}--[0-9]{2}-[0-9]{2}-[0-9]{2})\.(.*)`),
		// ts layout: yyyy-mm-dd--hh-MM-ss
		saveTsLayout: "2006-01-02--15-04-05",
	}
}

type intakeHandler struct {
	s3c          *s3.Client
	s3bucket     string
	saveExpr     *regexp.Regexp
	saveTsLayout string
}

func (h *intakeHandler) Handle(i common.Input) (int, error) {
	game := i.Params.ByName("game")
	client := i.Params.ByName("client")
	save := i.Params.ByName("save")
	saveSize := i.Request.ContentLength

	if saveSize == 0 {
		return http.StatusBadRequest, errors.New("content length zero is not allowed")
	}
	if saveSize < 0 { // -1 means unknown
		return http.StatusBadRequest, errors.New("unkown content length is not allowed")
	}
	// TODO: make this configurable
	if saveSize > 10_000_000 {
		i.Logger.Warn("save size exceeds maximum", zap.Int64("saveSize", saveSize))
		return http.StatusRequestEntityTooLarge, errors.New("save size exceeds maximum")
	}

	if game != "silksong" && game != "hollowknight" {
		i.Logger.Warn("unrecognized game", zap.String("game", game))
		return http.StatusBadRequest, errors.New("unrecognized game")
	}

	if !isValidUUID(client) {
		i.Logger.Warn("invalid client uuid", zap.String("clientId", client))
		return http.StatusBadRequest, errors.New("invalid client id")
	}

	saveMatch := h.saveExpr.FindStringSubmatch(save)
	if saveMatch == nil {
		i.Logger.Warn("invalid save path format", zap.String("save", save))
		return http.StatusBadRequest, errors.New("invalid save path format")
	}
	// saveName := saveMatch[1]
	saveTs := saveMatch[2]
	saveExt := saveMatch[3]

	saveTime, err := time.Parse(h.saveTsLayout, saveTs)
	if err != nil {
		i.Logger.Warn("failed to parse save time", zap.String("save", save), zap.String("saveTs", saveTs), zap.Error(err))
		return http.StatusBadRequest, errors.New("failed to parse save time")
	}

	if saveExt != "dat" {
		i.Logger.Warn("unrecognized save extension", zap.String("save", save), zap.String("saveExt", saveExt))
		return http.StatusBadRequest, errors.New("unrecognized save extension")
	}

	// TODO: is this even needed since we checked content length???
	saveBody := http.MaxBytesReader(i.Response, i.Request.Body, i.Request.ContentLength)

	s3key := fmt.Sprintf("game=%s/client=%s/%s", game, client, save)
	_, err = h.s3c.PutObject(i.Request.Context(), &s3.PutObjectInput{
		Bucket:        &h.s3bucket,
		Key:           &s3key,
		Body:          saveBody,
		ContentLength: saveSize,
	}, func(o *s3.Options) {
		o.RetryMaxAttempts = 1
	}, s3.WithAPIOptions(v4.SwapComputePayloadSHA256ForUnsignedPayloadMiddleware))
	if err != nil {
		i.Logger.Error("failed to upload to s3", zap.Error(err))
		return http.StatusInternalServerError, err
	}

	i.Logger.Debug(
		"save upload completed",
		zap.Time("saveTime", saveTime),
		zap.String("save", save),
		zap.String("client", client),
		zap.String("s3bucket", h.s3bucket),
		zap.String("s3key", s3key),
	)

	return http.StatusOK, nil
}

func isValidUUID(u string) bool {
	_, err := uuid.Parse(u)
	return err == nil
}
