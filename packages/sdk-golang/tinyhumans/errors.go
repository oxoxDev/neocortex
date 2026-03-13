package tinyhumans

import "fmt"

// TinyHumanError represents an error returned by the TinyHumans API.
type TinyHumanError struct {
	Message string
	Status  int
	Body    interface{}
}

func (e *TinyHumanError) Error() string {
	return fmt.Sprintf("TinyHumanError (status %d): %s", e.Status, e.Message)
}
