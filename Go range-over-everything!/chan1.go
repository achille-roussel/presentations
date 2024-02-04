package main

func main() {
	// START OMIT
	ch := make(chan int)
	go func() {
		defer close(ch) // HL
		for _, v := range []int{40, 41, 42} {
			ch <- v
		}
	}()
	for v := range ch { // HL
		println(v)
	}
	// END OMIT
}
