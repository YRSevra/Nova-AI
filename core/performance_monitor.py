"""
core/performance_monitor.py
Nova Performance Monitor
"""

import os
import time
import psutil


class PerformanceMonitor:

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()

    def report(self):

        cpu = self.process.cpu_percent(interval=0.2)

        ram = self.process.memory_info().rss / 1024 / 1024

        uptime = time.time() - self.start_time

        print("\n========== Nova Performance ==========")
        print(f"CPU Usage : {cpu:.1f}%")
        print(f"RAM Usage : {ram:.1f} MB")
        print(f"Uptime    : {uptime:.1f} sec")
        print("======================================\n")