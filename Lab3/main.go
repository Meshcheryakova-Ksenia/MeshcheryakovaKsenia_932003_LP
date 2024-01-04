package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"time"
)

type Token struct {
	Data      string
	Recipient int
	TTL       int
}

func node(id int, prev <-chan Token, next chan<- Token, end chan<- int) {
	for token := range prev {
		if token.TTL <= 0 {
			// Время жизни токена истекло
			end <- id
			return
		}
		if token.Recipient == id {
			fmt.Printf("Узел %d получил сообщение: %s\n", id, token.Data)
			end <- id
			return
		}
		token.TTL--
		// Пересылаем токен следующему узлу
		next <- token
	}
}

func main() {
	fmt.Print("Введите количество узлов (N): ")
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Scan()

	N, err := strconv.Atoi(scanner.Text())
	if err != nil || N <= 0 {
		fmt.Println("Неверное количество узлов. Введите положительное целое число")
		return
	}

	// Создаем каналы для передачи токена и сигнала об окончании
	channels := make([]chan Token, N)
	for i := range channels {
		channels[i] = make(chan Token)
	}

	// Канал для приема сигнала, когда сообщение достигает получателя или время его жизни истекает
	end := make(chan int)

	// Запускаем горутины для каждого узла
	for i := 0; i < N; i++ {
		go node(i, channels[i], channels[(i+1)%N], end)
	}

	// Создаем токен
	fmt.Print("Введите сообщение для отправки: ")
	scanner.Scan()
	data := scanner.Text()

	fmt.Print("Введите номер получателя узла (0 to N-1): ")
	scanner.Scan()
	recipient, err := strconv.Atoi(scanner.Text())
	if err != nil || recipient < 0 || recipient >= N {
		fmt.Println("Неверный получатель")
		return
	}

	fmt.Print("Введите TTL (время жизни): ")
	scanner.Scan()
	ttl, err := strconv.Atoi(scanner.Text())
	if err != nil || ttl <= 0 {
		fmt.Println("Неверный TTL. Введите положительное целое число")
		return
	}

	// Отправляем токен первому узлу
	token := Token{Data: data, Recipient: recipient, TTL: ttl}
	channels[0] <- token

	nodeID := <-end
	if nodeID != recipient {
		fmt.Printf("Сообщение истекло на узле %d до достижения узла %d\n", nodeID, recipient)
	}

	// Закрываем все каналы перед выходом
	for i := range channels {
		close(channels[i])
	}

	// Даем немного времени всем горутинам для корректного завершения работы
	time.Sleep(1 * time.Second)
	fmt.Println("Эмуляция TokenRing завершена")
}
