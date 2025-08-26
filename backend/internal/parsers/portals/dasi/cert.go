package dasi

import (
	"crypto/x509"
	_ "embed"
)

//go:embed cert.pem
var certPEM []byte

var rootCAs *x509.CertPool

func init() {
	rootCAs = x509.NewCertPool()
	if !rootCAs.AppendCertsFromPEM(certPEM) {
		panic("failed to parse root certificate")
	}
}
