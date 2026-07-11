package consumer

type Config struct {
	URL        string
	Stream     string
	Subject    string
	Durable    string
	MaxDeliver int
}
