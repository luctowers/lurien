package common

import (
	"context"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

func awsStaticEnpointResolver(url string) aws.EndpointResolverWithOptionsFunc {
	return func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			URL:               url,
			HostnameImmutable: true,
		}, nil
	}
}

func NewS3(cfg *S3Config) (*s3.Client, error) {
	awscfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		return nil, err
	}
	if cfg.Endpoint != nil {
		awscfg.EndpointResolverWithOptions = awsStaticEnpointResolver(*cfg.Endpoint)
	}
	if cfg.Key != nil {
		// TODO: this check would probably be in the config validation at load
		if cfg.Secret == nil {
			return nil, fmt.Errorf("aws s3 access key requires secret")
		}
		awscfg.Credentials = credentials.NewStaticCredentialsProvider(*cfg.Key, *cfg.Secret, "")
	}
	s3c := s3.NewFromConfig(awscfg)
	return s3c, nil
}

type S3Config struct {
	Endpoint *string `mapstructure:"S3_ENDPOINT"`
	Key      *string `mapstructure:"S3_KEY"`
	Secret   *string `mapstructure:"S3_SECRET"`
}
