package main

import (
	"context"
	"errors"
	"net/http"
	"regexp"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
	"github.com/luctowers/lurien/common"
	"go.uber.org/zap"
)

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
	client := i.Params.ByName("client")
	save := i.Params.ByName("save")
	agent := i.Request.Header.Get("User-Agent")

	if agent != "lurien_client/1.0" {
		i.Logger.Warn("unrecognized user-agent", zap.String("userAgent", agent))
		return http.StatusBadRequest, errors.New("unrecognized user-agent")
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

	_, err := time.Parse(h.saveTsLayout, saveTs)
	if err != nil {
		i.Logger.Warn("failed to parse save time", zap.String("save", save), zap.String("saveTs", saveTs), zap.Error(err))
		return http.StatusBadRequest, errors.New("failed to parse save time")
	}

	if saveExt != "dat" {
		i.Logger.Warn("unrecognized save extension", zap.String("save", save), zap.String("saveExt", saveExt))
		return http.StatusBadRequest, errors.New("unrecognized save extension")
	}

	result, err := h.s3c.ListBuckets(context.TODO(), &s3.ListBucketsInput{})
	if err != nil {
		return http.StatusInternalServerError, err
	}
	i.Logger.Info("listing buckets")
	for _, bucket := range result.Buckets {
		i.Logger.Info(*bucket.Name)
	}

	return http.StatusOK, nil
}

func isValidUUID(u string) bool {
	_, err := uuid.Parse(u)
	return err == nil
}
