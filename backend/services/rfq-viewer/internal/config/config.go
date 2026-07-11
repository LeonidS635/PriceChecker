package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
	PGHost     string
	PGPort     string
	PGUser     string
	PGPassword string
	PGDatabase string
	PGSSLMode  string

	HTTPAddr       string
	NATSURL        string
	NATSStream     string
	NATSSubject    string
	NATSDurable    string
	NATSMaxDeliver int
}

func (c Config) PGDSN() string {
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=%s",
		c.PGUser, c.PGPassword, c.PGHost, c.PGPort, c.PGDatabase, c.PGSSLMode,
	)
}

func (c Config) validate() error {
	for _, item := range []struct {
		env   string
		value string
	}{
		{"RFQ_VIEWER_PG_HOST", c.PGHost},
		{"RFQ_VIEWER_PG_PORT", c.PGPort},
		{"RFQ_VIEWER_PG_USER", c.PGUser},
		{"RFQ_VIEWER_PG_PASSWORD", c.PGPassword},
		{"RFQ_VIEWER_PG_DB", c.PGDatabase},
		{"RFQ_VIEWER_HTTP_ADDR", c.HTTPAddr},
		{"RFQ_VIEWER_NATS_URL", c.NATSURL},
		{"RFQ_VIEWER_NATS_STREAM", c.NATSStream},
		{"RFQ_VIEWER_NATS_SUBJECT", c.NATSSubject},
		{"RFQ_VIEWER_NATS_DURABLE", c.NATSDurable},
	} {
		if item.value == "" {
			return fmt.Errorf("missing required env: %s", item.env)
		}
	}

	return nil
}

func Load() (Config, error) {
	cfg := Config{
		PGHost:     os.Getenv("RFQ_VIEWER_PG_HOST"),
		PGPort:     os.Getenv("RFQ_VIEWER_PG_PORT"),
		PGUser:     os.Getenv("RFQ_VIEWER_PG_USER"),
		PGPassword: os.Getenv("RFQ_VIEWER_PG_PASSWORD"),
		PGDatabase: os.Getenv("RFQ_VIEWER_PG_DB"),
		PGSSLMode:  os.Getenv("RFQ_VIEWER_PG_SSLMODE"),

		HTTPAddr:       os.Getenv("RFQ_VIEWER_HTTP_ADDR"),
		NATSURL:        os.Getenv("RFQ_VIEWER_NATS_URL"),
		NATSStream:     os.Getenv("RFQ_VIEWER_NATS_STREAM"),
		NATSSubject:    os.Getenv("RFQ_VIEWER_NATS_SUBJECT"),
		NATSDurable:    os.Getenv("RFQ_VIEWER_NATS_DURABLE"),
		NATSMaxDeliver: parseIntDefault(os.Getenv("RFQ_VIEWER_NATS_MAX_DELIVER"), 5),
	}

	if err := cfg.validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func parseIntDefault(value string, def int) int {
	if value == "" {
		return def
	}
	n, err := strconv.Atoi(value)
	if err != nil {
		return def
	}
	return n
}
