package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/go-playground/validator/v10"
	"github.com/luctowers/lurien/common"
	"github.com/spf13/viper"
	"go.uber.org/zap"

	"github.com/julienschmidt/httprouter"
)

func main() {
	cfg, err := loadConfig()
	if err != nil {
		log.Fatal(err)
	}
	logger, err := common.NewLogger(cfg.LogDebug)
	if err != nil {
		log.Fatal(err)
	}

	w := func(h common.Handler) httprouter.Handle {
		h = common.LoggingMiddleware(h)
		h = common.StatusMiddleware(h, cfg.HTTPDebug)
		return common.ToHTTPRouterHandle(h, logger)
	}

	router := httprouter.New()
	router.PUT("/api/intake/v1/client/:client/save/:save", w(Intake()))
	http.Handle("/", router)

	logger.Info("starting intake service", zap.Uint16("port", cfg.HTTPPort))
	err = http.ListenAndServe(fmt.Sprintf(":%d", cfg.HTTPPort), nil)
	if err != nil {
		logger.Fatal("failed to listen on port", zap.Error(err), zap.Uint16("port", cfg.HTTPPort))
	}
}

type Config struct {
	LogDebug   bool    `mapstructure:"LOG_DEBUG"`
	HTTPDebug  bool    `mapstructure:"HTTP_DEBUG"`
	HTTPPort   uint16  `mapstructure:"HTTP_PORT"`
	S3Endpoint *string `mapstructure:"S3_ENDPOINT"`
	S3Key      *string `mapstructure:"S3_KEY"`
	S3Secret   *string `mapstructure:"S3_SECRET"`
	S3Bucket   *string `mapstructure:"S3_BUCKET" validate:"required"`
}

func loadConfig() (*Config, error) {
	cfg := &Config{}
	v := viper.New()
	common.AutoBindEnv(v, *cfg)

	v.SetDefault("LOG_DEBUG", false)
	v.SetDefault("HTTP_DEBUG", false)
	v.SetDefault("HTTP_PORT", 80)

	err := v.UnmarshalExact(cfg)
	if err != nil {
		return nil, err
	}

	validate := validator.New()
	err = validate.Struct(cfg)
	if err != nil {
		return nil, err
	}

	return cfg, nil
}
