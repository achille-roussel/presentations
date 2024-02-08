package main

func main() {
	// START OMIT
	for _, v := range []string{"A", "B", "C"} { // HL
		go func() {
			print(v) // HL
		}()
	}
	// END OMIT
}
