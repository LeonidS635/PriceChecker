package utils

import (
	"io"
	"net/http"
	"strings"

	"github.com/gocolly/colly/v2"
)

func VisitIgnoringStatusCode(code int, c *colly.Collector, url string) error {
	if err := c.Visit(url); err != nil && !strings.Contains(err.Error(), http.StatusText(code)) {
		return err
	}
	return nil
}

func PostIgnoringStatusCode(code int, c *colly.Collector, url string, body map[string]string) error {
	if err := c.Post(url, body); err != nil && !strings.Contains(err.Error(), http.StatusText(code)) {
		return err
	}
	return nil
}

func RequestIgnoringStatusCode(
	code int, c *colly.Collector, method string, url string, body io.Reader, ctx *colly.Context, header http.Header,
) error {
	if err := c.Request(method, url, body, ctx, header); err != nil && !strings.Contains(err.Error(), http.StatusText(code)) {
		return err
	}
	return nil
}
