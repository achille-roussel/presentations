//go:build !durable

//go:generate coroc

package main

import (
	"errors"
	"flag"
	"io/fs"
	"log"
	"os"

	"github.com/dispatchrun/coroutine"
)

func work() {
	for i := 0; ; i++ {
		coroutine.Yield[int, any](i)
	}
}

func main() {
	var state string
	flag.StringVar(&state, "state", "coroutine.state", "Location of the coroutine state file")
	flag.Parse()

	coro := coroutine.New[int, any](work)

	if coroutine.Durable {
		b, err := os.ReadFile(state)
		if err != nil {
			if !errors.Is(err, fs.ErrNotExist) {
				log.Fatal(err)
			}
		} else if err := coro.Context().Unmarshal(b); err != nil {
			log.Fatal(err)
		}

		defer func() {
			if b, err := coro.Context().Marshal(); err != nil {
				log.Fatal(err)
			} else if err := os.WriteFile(state, b, 0666); err != nil {
				log.Fatal(err)
			}
		}()
	}

	if coro.Next() {
		println("yield:", coro.Recv())
	}
}
