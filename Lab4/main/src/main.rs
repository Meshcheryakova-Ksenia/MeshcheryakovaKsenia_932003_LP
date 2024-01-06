use std::env;
use std::fs::File;
use std::io::{self, Write, Read};
use std::time::Duration;
use std::thread;
use std::sync::mpsc;

fn main() {
    // Получаем URL из аргументов командной строки
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Использование: {} <URL>", args[0]);
        return;
    }
    let url = &args[1];

    let filename = url.split('/').last().unwrap_or("file.txt");

    // Запускаем скачивание файла
    match download_file(url, filename) {
        Ok(_) => println!("Файл успешно загружен"),
        Err(e) => eprintln!("Ошибка загрузки файла: {}", e),
    }
}

fn download_file(url: &str, filename: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Создаём HTTP-клиент
    let client = reqwest::blocking::Client::new();

    // Выполняем GET-запрос к URL
    let mut response = client.get(url).send()?;

    // Создаём файл для записи
    let mut file = File::create(filename)?;

    // Создаём буфер
    let mut buffer = [0; 1024];
    let mut total_bytes = 0;

    let (tx, rx) = mpsc::channel();

    // Таймер для отображения прогресса
    let timer_handle = thread::spawn(move || {
        let mut last_reported = 0;
        loop {
            match rx.recv_timeout(Duration::from_secs(1)) {
                Ok(bytes) => {
                    // Выводим прогресс загрузки
                    last_reported = bytes;
                    println!("Загружено: {} байт", bytes);
                }
                Err(mpsc::RecvTimeoutError::Timeout) => {
                    // Если в канале нет сообщений и прошла 1 секунда, выводим последнее сообщение
                    println!("Скачано (за последнюю секунду): {} байт", last_reported);
                }
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    // Если канал закрыт, завершаем цикл
                    println!("Загрузка завершена");
                    break;
                }
            }
        }
    });

    // Считывание данных из HTTP-ответа и запись в файл
    while let Ok(n) = response.read(&mut buffer) {
        if n == 0 { break; } // Выходим из цикла если больше нет данных
        file.write_all(&buffer[..n])?;
        total_bytes += n;
        // Отправляем обновленное количество байт в поток для вывода информации
        tx.send(total_bytes)?;
    }

    // Закрываем канал, чтобы сообщить о завершении загрузки
    drop(tx);

    if timer_handle.join().is_err() {
        eprintln!("Поток отслеживания прогресса завершился из-за ошибки");
    }

    println!("Финальный размер: {} байт", total_bytes);

    Ok(())
} 
