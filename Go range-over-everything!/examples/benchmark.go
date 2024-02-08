package main

import "testing"

// START OLD OMIT
func BenchmarkOld(b *testing.B) {
	for i := 0; i < b.N; i++ {
		// ...
	}
}

// END OLD OMIT

// START NEW OMIT
func BenchmarkNew(b *testing.B) {
	for i := range b.N { // HL
		// ...
	}
}

// END NEW OMIT
