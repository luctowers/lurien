package main

import (
	"errors"
	"log"
	"net/http"
	"regexp"
	"time"

	"github.com/luctowers/lurien/intake/handler"
	"go.uber.org/zap"

	"github.com/julienschmidt/httprouter"
)

const HttpDebug = true // TODO: this should not be true in production

func main() {
	logger, err := zap.NewProduction()
	if err != nil {
		log.Fatal(err)
	}

	w := func(h handler.Handler) httprouter.Handle {
		h = handler.LoggingMiddleware(h)
		h = handler.StatusMiddleware(h, HttpDebug)
		return handler.ToHTTPRouterHandle(h, logger)
	}

	router := httprouter.New()
	router.PUT("/api/intake/v1/client/:client/save/:save", w(Intake()))
	http.Handle("/", router)
	err = http.ListenAndServe(":8080", nil)
	if err != nil {
		logger.Fatal("failed to listen on port", zap.Error(err))
	}
}

func Intake() handler.Handler {
	return &intakeHandler{
		// save format: name---ts.ext
		saveExpr: regexp.MustCompile(`(.*)---([0-9]{4}-[0-9]{2}-[0-9]{2}--[0-9]{2}-[0-9]{2}-[0-9]{2})\.(.*)`),
		// ts layout: yyyy-mm-dd--hh-MM-ss
		saveTsLayout: "2006-01-02--15-04-05",
	}
}

type intakeHandler struct {
	saveExpr     *regexp.Regexp
	saveTsLayout string
}

func (h *intakeHandler) Handle(i handler.Input) (int, error) {
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
		i.Logger.Warn("invalid save format", zap.String("save", save))
		return http.StatusBadRequest, errors.New("invalid save format")
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

	return http.StatusOK, nil
}
