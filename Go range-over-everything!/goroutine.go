package main

import "sync"

func main() {
	// START OMIT
	wg := sync.WaitGroup{}
	for _, v := range []string{"A", "B", "C"} { // HL
		wg.Add(1)
		go func() {
			print(v) // HL
			wg.Done()
		}()
	}
	wg.Wait()
	// END OMIT
}
