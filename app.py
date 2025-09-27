import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import queue
import sys

from main import main_multi_agent_system  # adjust import
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class RedirectText(object):
    def __init__(self, text_widget, chart_updater):
        self.text_widget = text_widget
        self.chart_updater = chart_updater

    def write(self, string):
        self.text_widget.configure(state="normal")

        if "Routing Agent:" in string:
            self.text_widget.insert(tk.END, string, "routing")
        elif "Disaster Agent:" in string:
            self.text_widget.insert(tk.END, string, "disaster")
        elif "Medical Agent:" in string:
            self.text_widget.insert(tk.END, string, "medical")
        elif "Crime Agent:" in string:
            self.text_widget.insert(tk.END, string, "crime")
        elif "You:" in string:
            self.text_widget.insert(tk.END, string, "user")
        else:
            self.text_widget.insert(tk.END, string)
        
        if string.strip().startswith("[Metrics]"):
            try:
                # Example: "[Metrics] Initial request size: 0.0166 KB"
                parts = string.replace("[Metrics]", "").strip().split(":")
                stage = parts[0].strip()
                value = float(parts[1].strip().split()[0])  # grab numeric KB
                self.chart_updater(stage, value)
            except Exception:
                # Fallback: just print normally
                self.text_widget.insert(tk.END, string + "\n")

        
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass


class EmergencyUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚨 Multi-Agent Emergency System")

        # Output area
        self.text_area = ScrolledText(root, wrap=tk.WORD, height=25, width=80, bg="black", fg="white", font=("Consolas", 11))
        self.text_area.pack(padx=10, pady=10)
        self.text_area.configure(state="disabled")

        self.text_area.tag_config("routing", foreground="cyan")
        self.text_area.tag_config("medical", foreground="blue")
        self.text_area.tag_config("crime", foreground="red")
        self.text_area.tag_config("disaster", foreground="orange")
        self.text_area.tag_config("user", foreground="white")

        # Input area
        self.entry = tk.Entry(root, width=60, font=("Consolas", 11))
        self.entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_input)

        self.send_button = tk.Button(root, text="Send", command=self.send_input)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=5)

        # Metrics chart
        self.fig, self.ax = plt.subplots(figsize=(5, 2), dpi=100)
        self.ax.set_title("📊 Metrics Over Time")
        self.ax.set_ylabel("KB")
        self.ax.set_xlabel("Updates")

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.X, padx=10, pady=5)

        # Store metrics history
        self.metrics = {}

        def chart_updater(stage, value):
            if stage not in self.metrics:
                self.metrics[stage] = []
            self.metrics[stage].append(value)
            self.update_chart()
        
        # Queue for communication
        self.input_queue = queue.Queue()
        sys.stdin = self  # redirect stdin
        sys.stdout = RedirectText(self.text_area, chart_updater)  # redirect stdout

        # Run your system in a thread
        threading.Thread(target=main_multi_agent_system, daemon=True).start()
    
    def update_chart(self):
        self.ax.clear()
        self.ax.set_title("📊 Metrics Over Time")
        self.ax.set_ylabel("KB")
        self.ax.set_xlabel("Updates")

        for stage, values in self.metrics.items():
            self.ax.plot(values, marker="o", label=stage)

        self.ax.legend()
        self.canvas.draw()

    # stdin simulation
    def readline(self):
        return self.input_queue.get() + "\n"

    def send_input(self, event=None):
        user_input = self.entry.get().strip()
        if user_input:
            self.text_area.configure(state="normal")
            self.text_area.insert(tk.END, f"> {user_input}\n")
            self.text_area.configure(state="disabled")
            self.input_queue.put(user_input)
            self.entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = EmergencyUI(root)
    root.mainloop()
