package tinyhumans

import (
	"testing"
	"time"
)

func floatPtr(v float64) *float64 { return &v }

func TestValidateTimestamp(t *testing.T) {
	now := float64(time.Now().Unix())

	tests := []struct {
		name    string
		value   *float64
		field   string
		wantErr bool
	}{
		{"nil value", nil, "ts", false},
		{"negative value", floatPtr(-1), "ts", true},
		{"zero value", floatPtr(0), "ts", false},
		{"valid current timestamp", floatPtr(now), "ts", false},
		{"too far in future", floatPtr(now + 101*365*24*60*60), "ts", true},
		{"within 100 years", floatPtr(now + 50*365*24*60*60), "ts", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateTimestamp(tt.value, tt.field)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateTimestamp() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestValidateTimestamps(t *testing.T) {
	now := float64(time.Now().Unix())
	earlier := now - 1000
	later := now + 1000

	tests := []struct {
		name      string
		createdAt *float64
		updatedAt *float64
		wantErr   bool
	}{
		{"both nil", nil, nil, false},
		{"only createdAt set", floatPtr(now), nil, false},
		{"only updatedAt set", nil, floatPtr(now), false},
		{"updatedAt >= createdAt", floatPtr(earlier), floatPtr(later), false},
		{"updatedAt == createdAt", floatPtr(now), floatPtr(now), false},
		{"updatedAt < createdAt", floatPtr(later), floatPtr(earlier), true},
		{"negative createdAt", floatPtr(-1), floatPtr(now), true},
		{"negative updatedAt", floatPtr(now), floatPtr(-1), true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateTimestamps(tt.createdAt, tt.updatedAt)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateTimestamps() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}
