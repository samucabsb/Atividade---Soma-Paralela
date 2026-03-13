import os
import sys
import time
import threading
from typing import Callable

# ──────────────────────────────────────────────
# Constantes de tuning
# ──────────────────────────────────────────────

# Tamanho do bloco de leitura em bytes por thread.
# 512 KiB equilibra uso de memória e chamadas de sistema.
BLOCK_SIZE: int = 512 * 1024  # 512 KiB

# Intervalo de linhas entre cada atualização do progresso.
# Valores menores deixam o progresso mais suave, mas aumentam
# a frequência de escrita no terminal (custo negligenciável aqui).
PROGRESS_INTERVAL: int = 100_000

# Nome padrão do arquivo (pode ser sobrescrito na chamada).
DEFAULT_FILENAME: str = "numero2.txt"


# ──────────────────────────────────────────────
# Função auxiliar: divisão do arquivo em fatias
# ──────────────────────────────────────────────

def compute_byte_ranges(filepath: str, n_threads: int) -> list[tuple[int, int]]:
    """
    Divide o arquivo em `n_threads` fatias de bytes aproximadamente iguais.

    Cada fatia começa logo após uma quebra de linha para garantir que nenhuma
    linha seja partida entre duas threads. A última fatia vai até o fim do arquivo.

    Retorna uma lista de tuplas (start_byte, end_byte) — end_byte exclusivo,
    ou -1 para indicar "até o fim do arquivo".
    """
    file_size = os.path.getsize(filepath)

    if file_size == 0:
        return []

    # Tamanho nominal de cada fatia
    chunk_size = file_size // n_threads

    ranges: list[tuple[int, int]] = []
    start = 0

    with open(filepath, "rb") as fh:
        for i in range(n_threads):
            if i == n_threads - 1:
                # Última thread: lê até o fim
                ranges.append((start, -1))
                break

            # Posição nominal de corte
            end = start + chunk_size

            # Avança até a próxima quebra de linha para não cortar uma linha no meio
            fh.seek(end)
            fh.readline()          # descarta até o '\n' mais próximo
            end = fh.tell()        # posição real após a quebra

            ranges.append((start, end))
            start = end

            # Se o arquivo acabou antes, as threads restantes ficam vazias
            if start >= file_size:
                break

    return ranges


# ──────────────────────────────────────────────
# Worker: cada thread executa esta função
# ──────────────────────────────────────────────

def worker_thread(
    filepath: str,
    start_byte: int,
    end_byte: int,          # -1 == até o fim
    results: list,
    index: int,
    line_counter: list,     # list[int] de 1 elemento — contagem compartilhada (sem lock)
) -> None:
    """
    Lê o trecho [start_byte, end_byte) do arquivo e soma todos os inteiros.

    Decisões de performance:
      • Arquivo aberto no modo binário e lido em blocos (BLOCK_SIZE) para
        maximizar throughput de disco e minimizar chamadas de sistema.
      • A decodificação e o split são feitos sobre o buffer acumulado apenas
        quando há uma linha completa disponível (técnica de "leftover buffer").
      • `int()` é chamado diretamente sobre bytes (sem passar por str quando
        possível), mas Python ainda exige str para inteiros arbitrários — o
        decode é feito uma única vez por linha.
      • Soma local sem nenhum lock; resultado gravado em `results[index]`
        apenas ao terminar.
    """
    local_sum: int = 0
    local_count: int = 0
    leftover: bytes = b""

    with open(filepath, "rb") as fh:
        fh.seek(start_byte)
        bytes_remaining = (end_byte - start_byte) if end_byte != -1 else None

        while True:
            # Determina quantos bytes ler nesta iteração
            if bytes_remaining is not None:
                to_read = min(BLOCK_SIZE, bytes_remaining)
                if to_read <= 0:
                    break
            else:
                to_read = BLOCK_SIZE

            chunk = fh.read(to_read)
            if not chunk:
                break

            if bytes_remaining is not None:
                bytes_remaining -= len(chunk)

            # Combina sobra do bloco anterior com o novo chunk
            data = leftover + chunk

            # Encontra a última quebra de linha para não processar linha incompleta
            last_newline = data.rfind(b"\n")

            if last_newline == -1:
                # Nenhuma linha completa ainda — acumula tudo como sobra
                leftover = data
                continue

            # Processa todas as linhas completas
            complete = data[: last_newline]
            leftover = data[last_newline + 1 :]

            # split() lida corretamente com \r\n, espaços e linhas em branco
            for token in complete.split():
                local_sum += int(token)
                local_count += 1

            # Atualiza contador de progresso (sem lock; write atômica em CPython)
            line_counter[0] += local_count
            local_count = 0

        # Processa possível sobra final (última linha sem '\n')
        for token in leftover.split():
            local_sum += int(token)
            local_count += 1

        line_counter[0] += local_count

    # Grava resultado parcial na posição reservada para esta thread
    results[index] = local_sum


# ──────────────────────────────────────────────
# Monitor de progresso
# ──────────────────────────────────────────────

def progress_monitor(
    line_counter: list,      # list[int] compartilhado com os workers
    stop_event: threading.Event,
    total_lines_hint: int,   # estimativa para exibir percentual (0 = desconhecido)
) -> None:
    """
    Thread dedicada ao monitoramento de progresso.

    Acorda a cada 0,5 s e exibe o total de linhas processadas até o momento.
    Usa `\\r` para sobrescrever a linha anterior no terminal, sem gerar spam.
    O custo desta thread é mínimo pois ela dorme quase todo o tempo.
    """
    last_shown = -1

    while not stop_event.is_set():
        time.sleep(0.5)

        current = line_counter[0]

        # Exibe apenas quando o progresso avançou pelo menos PROGRESS_INTERVAL linhas
        if current - last_shown >= PROGRESS_INTERVAL:
            if total_lines_hint > 0:
                pct = min(current / total_lines_hint * 100, 99.9)
                msg = f"\rProgresso: {current:>12,} linhas processadas  ({pct:5.1f}%)"
            else:
                msg = f"\rProgresso: {current:>12,} linhas processadas"

            sys.stdout.write(msg)
            sys.stdout.flush()
            last_shown = current

    # Exibe o total final
    final = line_counter[0]
    if total_lines_hint > 0:
        msg = f"\rProgresso: {final:>12,} linhas processadas  (100.0%)\n"
    else:
        msg = f"\rProgresso: {final:>12,} linhas processadas\n"

    sys.stdout.write(msg)
    sys.stdout.flush()


# ──────────────────────────────────────────────
# Estimativa rápida do número de linhas
# ──────────────────────────────────────────────

def estimate_line_count(filepath: str, sample_bytes: int = 65_536) -> int:
    """
    Estima o número de linhas do arquivo lendo apenas os primeiros `sample_bytes`.

    Usado exclusivamente para exibir o percentual no monitor de progresso.
    Não afeta a correção da soma.
    """
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return 0

    sample_size = min(sample_bytes, file_size)
    with open(filepath, "rb") as fh:
        sample = fh.read(sample_size)

    newlines = sample.count(b"\n")
    if newlines == 0:
        return 0

    avg_line_bytes = sample_size / newlines
    return int(file_size / avg_line_bytes)


# ──────────────────────────────────────────────
# Função principal
# ──────────────────────────────────────────────

def main() -> None:
    """
    Ponto de entrada do programa.

    Fluxo:
      1. Solicita nome do arquivo e número de threads ao usuário.
      2. Divide o arquivo em byte ranges.
      3. Inicia as threads workers e o monitor de progresso.
      4. Aguarda conclusão e agrega resultados.
      5. Exibe soma total, tempo e threads utilizadas.
    """

    # ── Entrada do usuário ──────────────────────────────────────────────────
    print("=" * 55)
    print("  Soma Paralela de Inteiros — Trabalho de Paralelismo")
    print("=" * 55)

    filepath = input(f"\nNome do arquivo [{DEFAULT_FILENAME}]: ").strip()
    if not filepath:
        filepath = DEFAULT_FILENAME

    if not os.path.isfile(filepath):
        print(f"\n[ERRO] Arquivo '{filepath}' não encontrado.")
        sys.exit(1)

    while True:
        try:
            n_threads = int(input("Quantas threads deseja usar? ").strip())
            if n_threads < 1:
                raise ValueError
            break
        except ValueError:
            print("  → Digite um inteiro positivo (ex: 1, 2, 4, 8).")

    print()

    # ── Preparação ──────────────────────────────────────────────────────────
    file_size_mb = os.path.getsize(filepath) / (1024 ** 2)
    print(f"Arquivo  : {filepath}  ({file_size_mb:.1f} MB)")
    print(f"Threads  : {n_threads}")
    print("-" * 55)

    # Estimativa de linhas para o monitor de progresso (não crítica)
    estimated_lines = estimate_line_count(filepath)

    # Divide o arquivo em fatias de bytes, uma por thread
    byte_ranges = compute_byte_ranges(filepath, n_threads)
    actual_threads = len(byte_ranges)   # pode ser menor se o arquivo for pequeno

    # ── Estruturas compartilhadas ────────────────────────────────────────────
    # results[i] receberá a soma parcial da thread i (sem lock)
    results: list[int] = [0] * actual_threads

    # Contador de linhas processadas: lista com 1 int para permitir escrita
    # "in-place" pelas threads (CPython garante atomicidade em operações simples
    # de incremento de int, embora isso não seja garantia formal da linguagem —
    # para contagem aproximada de progresso é suficiente).
    line_counter: list[int] = [0]

    # Evento para sinalizar ao monitor de progresso que os workers terminaram
    stop_event = threading.Event()

    # ── Criação das threads ──────────────────────────────────────────────────
    workers: list[threading.Thread] = []
    for i, (start, end) in enumerate(byte_ranges):
        t = threading.Thread(
            target=worker_thread,
            args=(filepath, start, end, results, i, line_counter),
            daemon=True,
            name=f"worker-{i}",
        )
        workers.append(t)

    monitor = threading.Thread(
        target=progress_monitor,
        args=(line_counter, stop_event, estimated_lines),
        daemon=True,
        name="progress-monitor",
    )

    # ── Execução e medição de tempo ──────────────────────────────────────────
    t_start = time.perf_counter()

    monitor.start()
    for t in workers:
        t.start()

    # Aguarda todos os workers terminarem
    for t in workers:
        t.join()

    # Sinaliza ao monitor para exibir o total final e encerrar
    stop_event.set()
    monitor.join()

    t_end = time.perf_counter()

    # ── Agregação dos resultados parciais ────────────────────────────────────
    # Operação O(n_threads) — custo desprezível
    total_sum: int = sum(results)
    elapsed: float = t_end - t_start

    # ── Saída ────────────────────────────────────────────────────────────────
    print("-" * 55)
    print(f"Soma total       : {total_sum}")
    print(f"Tempo total      : {elapsed:.6f} segundos")
    print(f"Threads utilizadas: {actual_threads}")
    print("=" * 55)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()