package credentialscache

import (
	"encoding/json"
	"log"
	"os"
	"sync"

	"github.com/LeonidS635/PriceChecker/backend/internal/domain"
	"github.com/LeonidS635/PriceChecker/backend/internal/dto"
)

// TODO: Temporary fix. Need to replace it with separate users authentication service that will store all credentials.

type CredentialsCache struct {
	mu          *sync.Mutex
	credentials map[domain.PortalID]dto.Credentials
}

func NewCredentialsCache() CredentialsCache {
	f, err := os.OpenFile(
		"internal/parsers/workflow/credentialscache/credentials_cache.json", os.O_RDONLY|os.O_CREATE, 0666,
	)
	if err != nil {
		log.Println(err)
		return CredentialsCache{
			mu:          &sync.Mutex{},
			credentials: make(map[domain.PortalID]dto.Credentials),
		}
	}

	creds := make(map[domain.PortalID]dto.Credentials)
	_ = json.NewDecoder(f).Decode(&creds)

	return CredentialsCache{mu: &sync.Mutex{}, credentials: creds}
}

func (c CredentialsCache) Save(portalID domain.PortalID, credentials dto.Credentials) {
	c.mu.Lock()
	c.credentials[portalID] = credentials
	c.mu.Unlock()
}

func (c CredentialsCache) Get(portalID domain.PortalID) (dto.Credentials, bool) {
	c.mu.Lock()
	creds, ok := c.credentials[portalID]
	c.mu.Unlock()
	return creds, ok
}

func (c CredentialsCache) DumpInFile() {
	f, err := os.OpenFile(
		"internal/parsers/workflow/credentialscache/credentials_cache.json", os.O_WRONLY|os.O_TRUNC, 0666,
	)
	if err != nil {
		log.Println(err)
		return
	}

	c.mu.Lock()
	_ = json.NewEncoder(f).Encode(c.credentials)
	c.mu.Unlock()
}
