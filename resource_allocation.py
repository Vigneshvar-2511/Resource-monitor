import psutil
from datetime import datetime
import pandas as pd
import os
import tkinter as tk
from tkinter import ttk
import tkinter.font

def get_size(bytes):
    if bytes is None:
        return "N/A"
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

def get_processes_info():
    processes = []
    for process in psutil.process_iter():
        with process.oneshot():
            pid = process.pid
            if pid == 0:
                continue
            name = process.name()
            try:
                create_time = datetime.fromtimestamp(process.create_time())
            except OSError:
                create_time = datetime.fromtimestamp(psutil.boot_time())
            try:
                cores = len(process.cpu_affinity())
            except psutil.AccessDenied:
                cores = 0
            try:
                cpu_usage = process.cpu_percent()
            except psutil.AccessDenied:
                cpu_usage = 0
            status = process.status()
            try:
                nice = int(process.nice())
            except psutil.AccessDenied:
                nice = 0
            try:
                memory_info = process.memory_info()
                memory_usage = memory_info.rss
            except psutil.AccessDenied:
                memory_usage = 0
            io_counters = process.io_counters()
            read_bytes = io_counters.read_bytes
            write_bytes = io_counters.write_bytes
            n_threads = process.num_threads()
            try:
                username = process.username()
            except psutil.AccessDenied:
                username = "N/A"
            
        processes.append({
            'pid': pid, 'name': name, 'create_time': create_time,
            'cores': cores, 'cpu_usage': cpu_usage, 'status': status,
            'memory_usage': memory_usage, 'read_bytes': read_bytes, 'write_bytes': write_bytes,
            'n_threads': n_threads, 'username': username,
        })

    return processes



def construct_dataframe(processes):
    df = pd.DataFrame(processes)
    df.set_index('pid', inplace=True)
    df.sort_values(sort_by, inplace=True, ascending=not descending)
    
    # Handle cases where memory information is not accessible
    df['memory_usage'] = df['memory_usage'].apply(lambda x: get_size(x) if x != 0 else "N/A")
    
    df['write_bytes'] = df['write_bytes'].apply(get_size)
    df['read_bytes'] = df['read_bytes'].apply(get_size)
    df['create_time'] = df['create_time'].apply(datetime.strftime, args=("%Y-%m-%d %H:%M:%S",))
    df = df[columns.split(",")]
    return df

def update_info():
    processes = get_processes_info()
    df = construct_dataframe(processes)
    total_memory = psutil.virtual_memory().percent
    total_cpu = psutil.cpu_percent()
    
    text.delete(1.0, tk.END)
    text.insert(tk.END, f"Total Memory Usage: {total_memory:.2f}%\n")
    text.insert(tk.END, f"Total CPU Usage: {total_cpu:.2f}%\n\n")
    
    text.insert(tk.END, "Top 10 Processes by Memory Usage:\n")
    top_processes = df.head(10)
    text.insert(tk.END, top_processes.to_string())
    
    text.insert(tk.END, "\nCurrently Running Processes:\n")
    current_processes = df[~df.index.isin(top_processes.index)]
    text.insert(tk.END, current_processes.to_string())

def on_refresh_button_click():
    update_info()

columns = "name,cpu_usage,memory_usage,read_bytes,write_bytes,status,create_time,n_threads,cores"
sort_by = "memory_usage"
descending = False

root = tk.Tk()
root.title("Process Viewer & Monitor")

frame = ttk.Frame(root)
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

refresh_button = ttk.Button(frame, text="Refresh", command=on_refresh_button_click)
refresh_button.grid(row=0, column=0, sticky=(tk.W, tk.E))

text = tk.Text(frame, wrap="none", state="normal", width=180, height=80)
text.grid(row=1, column=0, sticky=(tk.W, tk.E))

update_info()

root.mainloop()
