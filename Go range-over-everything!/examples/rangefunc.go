package main

func main() {
	// START OMIT
	for v := range func(yield func(int) bool) { // HL
		for i := range 5 {
			if !yield(i) { // HL
				break
			}
		}
	} {
		println(v)
	}
	// END OMIT
}
