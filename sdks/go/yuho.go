// Package yuho provides a Go client for the Yuho legal DSL API.
package yuho

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Config holds client configuration.
type Config struct {
	BaseURL   string
	AuthToken string
	Timeout   time.Duration
}

// Client is a Yuho API client.
type Client struct {
	baseURL    string
	authToken  string
	httpClient *http.Client
}

// NewClient creates a new Yuho API client.
func NewClient(cfg Config) *Client {
	timeout := cfg.Timeout
	if timeout == 0 {
		timeout = 30 * time.Second
	}
	return &Client{
		baseURL:    cfg.BaseURL,
		authToken:  cfg.AuthToken,
		httpClient: &http.Client{Timeout: timeout},
	}
}

// APIResponse wraps all API responses.
type APIResponse struct {
	Success bool            `json:"success"`
	Data    json.RawMessage `json:"data,omitempty"`
	Error   *APIError       `json:"error,omitempty"`
}

// APIError is a structured error from the API.
type APIError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

func (e *APIError) Error() string { return fmt.Sprintf("%s: %s", e.Code, e.Message) }

func (c *Client) do(ctx context.Context, method, path string, body interface{}) (*APIResponse, error) {
	var reqBody io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reqBody = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+"/v1"+path, reqBody)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.authToken)
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var apiResp APIResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}
	if apiResp.Error != nil {
		return nil, apiResp.Error
	}
	return &apiResp, nil
}

// Parse parses Yuho source code.
func (c *Client) Parse(ctx context.Context, source string) (*APIResponse, error) {
	return c.do(ctx, "POST", "/parse", map[string]string{"source": source})
}

// Validate validates Yuho source code.
func (c *Client) Validate(ctx context.Context, source string) (*APIResponse, error) {
	return c.do(ctx, "POST", "/validate", map[string]string{"source": source})
}

// Transpile transpiles Yuho source to a target format.
func (c *Client) Transpile(ctx context.Context, source, target string) (*APIResponse, error) {
	return c.do(ctx, "POST", "/transpile", map[string]interface{}{"source": source, "target": target})
}

// Health checks the server health.
func (c *Client) Health(ctx context.Context) (*APIResponse, error) {
	return c.do(ctx, "GET", "/health", nil)
}
