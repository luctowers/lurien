package main

import (
	"log"
	"net/http"

	"github.com/luctowers/lurien/lurien_intake/handler"
	"go.uber.org/zap"

	"github.com/julienschmidt/httprouter"
)

const HttpDebug = true

func main() {
	logger, err := zap.NewDevelopment()
	if err != nil {
		log.Fatal(err)
	}

	w := func(h handler.Handler) httprouter.Handle {
		h = handler.LoggingMiddleware(h)
		h = handler.StatusMiddleware(h, HttpDebug)
		return handler.ToHTTPRouterHandle(h, logger)
	}

	router := httprouter.New()
	router.PUT("/intake/v1/client/:client/save/:save", w(&IntakeHandler{}))
	http.Handle("/", router)
	http.ListenAndServe(":8080", nil)
}

type IntakeHandler struct{}

func (h *IntakeHandler) Handle(i handler.Input) (int, error) {
	return 200, nil
	// client := i.Params.ByName("client")
	// save := p.ByName("save")
	// agent := r.Header.Get("User-Agent")

	// if !isValidUUID(client) {
	// 	w.WriteHeader(http.StatusBadRequest)
	// 	return
	// }
}
