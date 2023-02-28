package common

import (
	"net/http"

	"github.com/julienschmidt/httprouter"
	"go.uber.org/zap"
)

type Input struct {
	Request  *http.Request
	Response http.ResponseWriter
	Params   httprouter.Params
	Logger   *zap.Logger
}

type Handler interface {
	Handle(Input) (int, error)
}

func ToHTTPRouterHandle(h Handler, l *zap.Logger) httprouter.Handle {
	return func(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {
		h.Handle(Input{
			Request:  r,
			Response: w,
			Params:   ps,
			Logger:   l,
		})
	}
}

func ToHTTPHandler(handle httprouter.Handle) http.Handler {
	return httpHandlerAdaptor{handle}
}

type httpHandlerAdaptor struct {
	handle httprouter.Handle
}

func (h httpHandlerAdaptor) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	h.handle(w, req, nil)
}

func StaticStatus(status int) Handler {
	return staticStatusHandler{status, nil}
}

func StaticStatusError(status int, err error) Handler {
	return staticStatusHandler{status, err}
}

type staticStatusHandler struct {
	status int
	err    error
}

func (h staticStatusHandler) Handle(i Input) (int, error) {
	return h.status, h.err
}
