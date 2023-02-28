package common

import (
	"errors"
	"net/http"

	"go.uber.org/zap"
)

type AgentFilterHandler struct {
	handler Handler
	agent   string
}

func AgentFilterMiddleware(handler Handler, agent string) Handler {
	return AgentFilterHandler{handler, agent}
}

func (h AgentFilterHandler) Handle(i Input) (int, error) {
	agent := i.Request.UserAgent()
	if agent != h.agent {
		i.Logger.Warn("unrecognized user-agent", zap.String("userAgent", agent))
		return http.StatusBadRequest, errors.New("unrecognized user-agent")
	}
	status, err := h.handler.Handle(i)
	return status, err
}
