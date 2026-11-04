import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import traceback

from Run_IBM_Hardware_BackEnd import (
    IBMHardwareRunner,
    MIN_N,
    MAX_N,
    DEFAULT_SHOTS,
    DEFAULT_CHANNEL,
    DEFAULT_BATCH_SIZE,
    MODE_DESCRIPTIONS
)

class QALUHardwareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QALU - IBM Quantum Hardware Exhaustive Testing")
        self.root.geometry("1050x800")
        self.root.minsize(950, 700)

        self.runner = IBMHardwareRunner()
        
        self.last_execution_data = None
        self.n_var = tk.IntVar(value=2)
        self.mode_var = tk.IntVar(value=3)
        self.shots_var = tk.IntVar(value=DEFAULT_SHOTS)
        self.batch_size_var = tk.IntVar(value=DEFAULT_BATCH_SIZE)
        self.channel_var = tk.StringVar(value=DEFAULT_CHANNEL)
        self.backend_var = tk.StringVar()
        self.token_var = tk.StringVar()
        
        self.create_widgets()
        self.update_workload_display()

    def create_widgets(self):
        title_frame = ttk.Frame(self.root, padding=10)
        title_frame.pack(fill="x")
        
        ttk.Label(
            title_frame, 
            text="QALU IBM Quantum Hardware Testing", 
            font=("Arial", 18, "bold")
        ).pack()
        
        ttk.Label(
            title_frame, 
            text="Exhaustive hardware evaluation of all 20 QALU operations", 
            font=("Arial", 10)
        ).pack(pady=(5, 0))

        connection_frame = ttk.LabelFrame(self.root, text="IBM Quantum Connection", padding=10)
        connection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(connection_frame, text="API Token:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.token_entry = ttk.Entry(connection_frame, textvariable=self.token_var, show="*", width=70)
        self.token_entry.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(connection_frame, text="Channel:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.channel_entry = ttk.Entry(connection_frame, textvariable=self.channel_var, width=30)
        self.channel_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(connection_frame, text="Backend:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.backend_entry = ttk.Entry(connection_frame, textvariable=self.backend_var, width=30)
        self.backend_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(
            connection_frame, 
            text="Leave Backend empty to automatically select the least-busy compatible real quantum computer.", 
            font=("Arial", 8)
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=(0, 5))

        settings_frame = ttk.LabelFrame(self.root, text="Experiment Configuration", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(settings_frame, text="Operand size n:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.n_spinbox = ttk.Spinbox(settings_frame, from_=MIN_N, to=MAX_N, textvariable=self.n_var, width=8)
        self.n_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.n_spinbox.bind("<KeyRelease>", lambda event: self.update_workload_display())
        self.n_spinbox.bind("<FocusOut>", lambda event: self.update_workload_display())

        ttk.Label(settings_frame, text="Shots per circuit:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.shots_spinbox = ttk.Spinbox(settings_frame, from_=1, to=100000, textvariable=self.shots_var, width=12)
        self.shots_spinbox.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.shots_spinbox.bind("<KeyRelease>", lambda event: self.update_workload_display())
        self.shots_spinbox.bind("<FocusOut>", lambda event: self.update_workload_display())

        ttk.Label(settings_frame, text="Circuits per IBM job:").grid(row=0, column=4, sticky="e", padx=5, pady=5)
        self.batch_spinbox = ttk.Spinbox(settings_frame, from_=1, to=1000, textvariable=self.batch_size_var, width=10)
        self.batch_spinbox.grid(row=0, column=5, sticky="w", padx=5, pady=5)

        mode_frame = ttk.LabelFrame(settings_frame, text="Toffoli Implementation", padding=8)
        mode_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=5, pady=8)
        
        ttk.Radiobutton(
            mode_frame, text="Mode 2 — Standard 7T Toffoli", variable=self.mode_var, value=2, 
            command=self.update_workload_display
        ).pack(anchor="w", pady=3)
        
        ttk.Radiobutton(
            mode_frame, text="Mode 3 — 4T Margolus Relative-Phase Toffoli", variable=self.mode_var, value=3, 
            command=self.update_workload_display
        ).pack(anchor="w", pady=3)

        workload_frame = ttk.LabelFrame(self.root, text="Exhaustive Workload", padding=10)
        workload_frame.pack(fill="x", padx=10, pady=5)

        self.required_qubits_label = ttk.Label(workload_frame)
        self.required_qubits_label.grid(row=0, column=0, sticky="w", padx=10, pady=4)

        self.input_pairs_label = ttk.Label(workload_frame)
        self.input_pairs_label.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        self.circuits_label = ttk.Label(workload_frame)
        self.circuits_label.grid(row=1, column=0, sticky="w", padx=10, pady=4)

        self.shots_label = ttk.Label(workload_frame)
        self.shots_label.grid(row=1, column=1, sticky="w", padx=10, pady=4)

        self.total_shots_label = ttk.Label(workload_frame)
        self.total_shots_label.grid(row=2, column=0, sticky="w", padx=10, pady=4)

        self.jobs_label = ttk.Label(workload_frame)
        self.jobs_label.grid(row=2, column=1, sticky="w", padx=10, pady=4)

        self.mode_label = ttk.Label(workload_frame)
        self.mode_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=4)

        self.warning_label = ttk.Label(workload_frame, wraplength=900)
        self.warning_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=6)

        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill="x")

        self.start_button = ttk.Button(button_frame, text="Start IBM Hardware Execution", command=self.start_execution)
        self.start_button.pack(side="left", padx=5)

        self.save_button = ttk.Button(button_frame, text="Save Last Result As...", command=self.save_last_result)
        self.save_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear Log", command=self.clear_log)
        self.clear_button.pack(side="left", padx=5)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=15, pady=(0, 5))

        log_frame = ttk.LabelFrame(self.root, text="Execution Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, wrap="word", font=("Consolas", 9))
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def update_workload_display(self):
        try:
            n = int(self.n_var.get())
            shots = int(self.shots_var.get())
            batch_size = int(self.batch_size_var.get())

            if n < MIN_N or n > MAX_N:
                raise ValueError
            if shots <= 0 or batch_size <= 0:
                raise ValueError

            workload = self.runner.calculate_workload(n, shots)
            total_circuits = workload["total_circuits"]
            number_jobs = (total_circuits + batch_size - 1) // batch_size

            self.required_qubits_label.config(text=f"Required QALU qubits: {workload['required_qubits']}")
            self.input_pairs_label.config(text=f"Input pairs: {workload['input_pairs']:,}")
            self.circuits_label.config(text=f"Total circuits: {total_circuits:,}")
            self.shots_label.config(text=f"Shots/circuit: {shots:,}")
            self.total_shots_label.config(text=f"Total shots: {workload['total_shots']:,}")
            self.jobs_label.config(text=f"Estimated IBM jobs: {number_jobs:,}")

            mode = self.mode_var.get()
            self.mode_label.config(text=f"Selected implementation: Mode {mode} — {MODE_DESCRIPTIONS[mode]}")

            if n <= 2:
                warning = "Suitable for the exhaustive n=2 hardware experiment."
            elif n == 3:
                warning = "n=3 requires 1,280 circuits. This is still a manageable exhaustive experiment, but requires more hardware execution time."
            elif n <= 5:
                warning = "Large exhaustive hardware workload. Execution time will depend strongly on IBM queue and backend availability."
            elif n <= 7:
                warning = "Very large exhaustive workload. Batch execution is required."
            else:
                warning = f"EXTREMELY LARGE workload. n={n} requires {total_circuits:,} circuits. The program uses batch processing, but this scale is generally not practical for a short free hardware experiment."
            
            self.warning_label.config(text=warning)

        except Exception:
            self.required_qubits_label.config(text="Required QALU qubits: --")
            self.input_pairs_label.config(text="Input pairs: --")
            self.circuits_label.config(text="Total circuits: --")
            self.shots_label.config(text="Shots/circuit: --")
            self.total_shots_label.config(text="Total shots: --")
            self.jobs_label.config(text="Estimated IBM jobs: --")
            self.mode_label.config(text="Selected implementation: --")
            self.warning_label.config(text="Enter valid values for n, shots and batch size.")

    def log(self, message):
        def append():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        self.root.after(0, append)

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def start_execution(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Missing API Token", "Please enter your IBM Quantum API token.")
            return

        try:
            n = int(self.n_var.get())
            shots = int(self.shots_var.get())
            batch_size = int(self.batch_size_var.get())
        except ValueError:
            messagebox.showerror("Invalid Configuration", "n, shots and batch size must be integers.")
            return

        if n < MIN_N or n > MAX_N:
            messagebox.showerror("Invalid n", "n must be between 1 and 12.")
            return
        if shots <= 0:
            messagebox.showerror("Invalid shots", "Shots must be greater than zero.")
            return
        if batch_size <= 0:
            messagebox.showerror("Invalid batch size", "Batch size must be greater than zero.")
            return

        mode = self.mode_var.get()
        if mode not in (2, 3):
            messagebox.showerror("Invalid mode", "Select Mode 2 or Mode 3.")
            return

        workload = self.runner.calculate_workload(n, shots)
        total_circuits = workload["total_circuits"]
        estimated_jobs = (total_circuits + batch_size - 1) // batch_size

        if total_circuits > 10000:
            answer = messagebox.askyesno(
                "Very Large Workload",
                f"n={n}\n\n"
                f"Circuits: {total_circuits:,}\n"
                f"Shots/circuit: {shots:,}\n"
                f"Total shots: {workload['total_shots']:,}\n\n"
                f"Estimated IBM jobs: {estimated_jobs:,}\n\n"
                "This is substantially larger than the n=2 experiment.\n\n"
                "Do you really want to continue?"
            )
            if not answer:
                return

        channel = self.channel_var.get().strip()
        backend_name = self.backend_var.get().strip() or None

        self.start_button.config(state="disabled")
        self.progress.start(10)

        self.log("")
        self.log("=" * 70)
        self.log("STARTING QALU IBM QUANTUM HARDWARE EXECUTION")
        self.log("=" * 70)
        self.log(f"n                  = {n}")
        self.log(f"Mode               = {mode}")
        self.log(f"Implementation     = {MODE_DESCRIPTIONS[mode]}")
        self.log(f"Shots/circuit      = {shots:,}")
        self.log(f"Required qubits    = {workload['required_qubits']}")
        self.log(f"Input pairs        = {workload['input_pairs']:,}")
        self.log(f"Total circuits     = {total_circuits:,}")
        self.log(f"Total shots        = {workload['total_shots']:,}")
        self.log(f"Batch size         = {batch_size:,}")
        self.log(f"Estimated IBM jobs = {estimated_jobs:,}")
        self.log("")
        self.log("Hardware methodology:")
        self.log("  Optimization level 3 = ON")
        self.log("  M3 mitigation        = OFF")
        self.log("  Readout correction   = OFF")
        self.log("  Dynamical decoupling = OFF")
        self.log("  Gate twirling        = OFF")
        self.log("  Measurement twirling = OFF")
        self.log("")

        worker = threading.Thread(
            target=self.execute_worker,
            args=(token, n, mode, shots, channel, backend_name, batch_size),
            daemon=True
        )
        worker.start()

    def execute_worker(self, token, n, mode, shots, channel, backend_name, batch_size):
        try:
            self.log("Connecting to IBM Quantum...")
            self.log("Generating and executing exhaustive QALU circuits...")

            result = self.runner.run_ibm_exhaustive(
                token=token,
                n=n,
                mode=mode,
                shots=shots,
                channel=channel,
                backend_name=backend_name,
                output_directory="ibm_results",
                save_results=True,
                batch_size=batch_size,
                optimization_level=3
            )

            self.last_execution_data = result

            self.log("")
            self.log("=" * 70)
            self.log("EXECUTION FINISHED")
            self.log(f"Backend: {result['hardware']['backend']}")
            self.log(f"Mode: {result['implementation']['mode']}")
            self.log(f"n: {result['experiment']['n']}")
            self.log(f"Circuits: {result['experiment']['total_circuits']:,}")
            self.log(f"Total shots: {result['experiment']['total_shots']:,}")
            self.log(f"IBM jobs: {result['execution']['number_of_jobs']}")
            total_time = result['execution']['total_execution_time_seconds']
            self.log(f"Total execution time: {total_time:.2f} seconds")
            self.log("")
            self.log("Raw results saved to:")
            self.log(str(result.get("output_file")))
            self.log("=" * 70)

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Execution Complete",
                    "IBM Quantum hardware execution completed.\n\n"
                    f"Backend: {result['hardware']['backend']}\n\n"
                    f"n = {result['experiment']['n']}\n"
                    f"Mode = {result['implementation']['mode']}\n\n"
                    f"IBM jobs = {result['execution']['number_of_jobs']}\n"
                    f"Total execution time = {result['execution']['total_execution_time_seconds']:.2f} seconds\n\n"
                    "Results were saved to:\n"
                    f"{result.get('output_file')}"
                )
            )

        except Exception as error:
            tb_str = traceback.format_exc()
            error_msg = str(error) if str(error) and str(error) != "None" else repr(error)

            self.log("")
            self.log("=" * 70)
            self.log("EXECUTION ERROR")
            self.log("=" * 70)

            self.log(tb_str)  # Logs full stack trace to GUI text window
    
            self.root.after(
               0, 
               lambda: messagebox.showerror("Execution Error", f"{error_msg}\n\nSee log for details.")
            )

        finally:
            self.root.after(0, self.execution_finished)

    def execution_finished(self):
        self.progress.stop()
        self.start_button.config(state="normal")

    def save_last_result(self):
        if self.last_execution_data is None:
            messagebox.showwarning("No Result", "There is no completed execution to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save QALU Hardware Result",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(self.last_execution_data, file, indent=2)

            messagebox.showinfo(
                "Saved",
                f"Execution summary saved to:\n{file_path}\n\n"
                "The complete raw result file is already stored in the ibm_results directory."
            )
        except Exception as error:
            messagebox.showerror("Save Error", str(error))

def main():
    root = tk.Tk()
    app = QALUHardwareApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()