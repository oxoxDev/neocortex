package tinyhumans

import (
	"strings"
	"testing"
)

func TestTinyHumanError_Error(t *testing.T) {
	e := &TinyHumanError{Message: "bad request", Status: 400}
	got := e.Error()
	want := "TinyHumanError (status 400): bad request"
	if got != want {
		t.Errorf("Error() = %q, want %q", got, want)
	}
}

func TestTinyHumanError_ImplementsError(t *testing.T) {
	var err error = &TinyHumanError{Message: "test", Status: 500}
	if !strings.Contains(err.Error(), "TinyHumanError") {
		t.Error("TinyHumanError does not implement error interface correctly")
	}
}

func TestTinyHumanError_DifferentStatuses(t *testing.T) {
	tests := []struct {
		status  int
		message string
	}{
		{401, "unauthorized"},
		{404, "not found"},
		{500, "internal server error"},
	}
	for _, tt := range tests {
		e := &TinyHumanError{Message: tt.message, Status: tt.status}
		got := e.Error()
		if !strings.Contains(got, tt.message) {
			t.Errorf("Error() missing message %q in %q", tt.message, got)
		}
		if !strings.Contains(got, string(rune('0'+tt.status/100))) {
			t.Errorf("Error() missing status %d in %q", tt.status, got)
		}
	}
}
