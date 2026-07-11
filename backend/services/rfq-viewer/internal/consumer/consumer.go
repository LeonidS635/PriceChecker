package consumer

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/consumer/dto"
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
	"github.com/nats-io/nats.go"
)

type rfqService interface {
	SaveRFQ(ctx context.Context, item domain.RFQ) error
}

type Consumer struct {
	nc         *nats.Conn
	js         nats.JetStreamContext
	subject    string
	stream     string
	durable    string
	maxDeliver int

	service rfqService
}

func New(cfg Config, service rfqService) (*Consumer, error) {
	nc, err := nats.Connect(cfg.URL)
	if err != nil {
		return nil, fmt.Errorf("nats connect: %w", err)
	}

	js, err := nc.JetStream()
	if err != nil {
		nc.Close()
		return nil, fmt.Errorf("nats jetstream: %w", err)
	}

	maxDeliver := cfg.MaxDeliver
	if maxDeliver <= 0 {
		maxDeliver = 5
	}

	return &Consumer{
		nc:         nc,
		js:         js,
		subject:    cfg.Subject,
		stream:     cfg.Stream,
		durable:    cfg.Durable,
		maxDeliver: maxDeliver,
		service:    service,
	}, nil
}

func (c *Consumer) ensureStream() error {
	_, err := c.js.AddStream(&nats.StreamConfig{
		Name:     c.stream,
		Subjects: []string{c.subject},
	})
	if err != nil {
		return fmt.Errorf("nats ensure stream: %w", err)
	}

	return nil
}

func (c *Consumer) Run(ctx context.Context) error {
	if err := c.ensureStream(); err != nil {
		return err
	}

	sub, err := c.js.Subscribe(
		c.subject,
		c.handle,
		nats.Durable(c.durable),
		nats.ManualAck(),
		nats.DeliverAll(),
		nats.MaxDeliver(c.maxDeliver),
		nats.MaxAckPending(1),
	)
	if err != nil {
		return fmt.Errorf("nats subscribe: %w", err)
	}
	defer sub.Unsubscribe()

	slog.Info("NATS consumer started", "subject", c.subject, "durable", c.durable)

	<-ctx.Done()

	slog.Info("NATS consumer stopping")
	return nil
}

func (c *Consumer) Close() {
	if c.nc != nil {
		c.nc.Drain()
	}
}

func (c *Consumer) handle(msg *nats.Msg) {
	var result dto.ExtractionResult
	if err := json.Unmarshal(msg.Data, &result); err != nil {
		slog.Error("failed to decode message", "err", err)
		c.giveUpOrRetry(msg)
		return
	}

	item, err := result.ToDomain()
	if err != nil {
		slog.Error("failed to map extraction result", "job_id", result.JobID, "client_id", result.ClientID, "err", err)
		c.giveUpOrRetry(msg)
		return
	}

	if err := c.service.SaveRFQ(context.Background(), item); err != nil {
		slog.Error("failed to save RFQ", "job_id", item.JobID, "client_id", item.ClientID, "err", err)
		c.giveUpOrRetry(msg)
		return
	}

	slog.Info("saved extraction result",
		"job_id", item.JobID,
		"client_id", item.ClientID,
		"parts", len(item.Parts),
	)

	if err := msg.Ack(); err != nil {
		slog.Error("failed to ack message", "err", err)
	}
}

func (c *Consumer) giveUpOrRetry(msg *nats.Msg) {
	numDelivered := uint64(1)
	if meta, err := msg.Metadata(); err == nil {
		numDelivered = meta.NumDelivered
	}

	if numDelivered >= uint64(c.maxDeliver) {
		slog.Error("giving up on message after delivery attempts", "attempts", numDelivered)
		if err := msg.Term(); err != nil {
			slog.Error("failed to term message", "err", err)
		}
		return
	}

	if err := msg.Nak(); err != nil {
		slog.Error("failed to nak message", "err", err)
	}
}
