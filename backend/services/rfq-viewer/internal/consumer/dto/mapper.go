package dto

import (
	"github.com/LeonidS635/PriceChecker/backend/services/rfq-viewer/internal/domain"
)

func (r ExtractionResult) ToDomain() (domain.RFQ, error) {
	return domain.RFQ{
		JobID:           r.JobID,
		ClientID:        r.ClientID,
		SenderEmail:     r.SenderEmail,
		SourceMessageID: r.SourceMessageID,
		Subject:         r.Subject,
		ReceivedAt:      r.ReceivedAt,
		ProcessedAt:     r.ProcessedAt,
		Parts:           toDomainParts(r.Parts),
	}, nil
}

func toDomainParts(parts []ExtractedPart) []domain.Part {
	result := make([]domain.Part, 0, len(parts))
	for _, part := range parts {
		result = append(result, domain.Part{
			PartNumber:   part.PartNumber,
			Description:  part.Description,
			Quantity:     part.Quantity,
			Alternatives: part.Alternatives,
		})
	}

	return result
}
