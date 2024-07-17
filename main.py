import _xxsubinterpreters as interpreters
import datetime
from threading import Thread
from time import sleep

import psutil

process = psutil.Process()

interpreter_ids = []
num_workers = 8

for i in range(num_workers):
    interpreter_ids.append(interpreters.create())

end_monitor = False

parallel_ram_mb = []
concurrent_ram_mb = []


def monitor_worker(ram_mb):
    global end_monitor
    while True:
        ram_mb.append(process.memory_info().rss / 1024 / 1024)
        if end_monitor:
            break
        sleep(1)


monitor = Thread(target=monitor_worker, args=(parallel_ram_mb,))
monitor.start()


def worker():
    i = 0
    end = 5000000
    while True:
        i += 1
        if i == end:
            break


print('### SUB INTERPRETERS THREADS ###')
to_join = []
for i, id in enumerate(interpreter_ids):
    t = Thread(target=interpreters.run_func, args=(id, worker))
    to_join.append(t)
    t.start()

start = datetime.datetime.now()
for i in to_join:
    i.join()
end = datetime.datetime.now()
parallel_time_s = (end - start).total_seconds()

for i in interpreter_ids:
    interpreters.destroy(i)
print('Interpreters destroyed')

end_monitor = True
monitor.join()
end_monitor = False

monitor = Thread(target=monitor_worker, args=(concurrent_ram_mb,))
monitor.start()

print('### CONVENTIONAL THREADS ###')
to_join = []
for i, id in enumerate(interpreter_ids):
    t = Thread(target=worker)
    to_join.append(t)
    t.start()

start = datetime.datetime.now()
for i in to_join:
    i.join()
end = datetime.datetime.now()
concurrent_time_s = (end - start).total_seconds()

end_monitor = True
monitor.join()

parallel_ram_avg = sum(parallel_ram_mb) / len(parallel_ram_mb)
concurrent_ram_avg = sum(concurrent_ram_mb) / len(concurrent_ram_mb)

print(f"""
Parallel run time:      {parallel_time_s}s ({parallel_time_s / concurrent_time_s * 100}% of concurrent run time)
Concurrent run time:    {concurrent_time_s}s

Parallel RAM usage avg: {parallel_ram_avg}MB ({parallel_ram_avg / concurrent_ram_avg * 100}% of concurrent RAM average) 
Concurrent RAM usage avg: {concurrent_ram_avg}MB 

""")
