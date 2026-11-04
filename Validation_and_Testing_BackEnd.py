import platform
import json
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

class ValidationAndTestingPackEnd:

    def get_hardware_info(self):
        info = {
            "OS": platform.system() + "\n" + platform.release(),
            "CPU": platform.processor(),
            "Cores": "Unknown",
            "RAM_Total": "Unknown",
            "RAM_Available": "Unknown"
        }
        if HAS_PSUTIL:
            info["Cores"] = str(psutil.cpu_count(logical=True))
            mem = psutil.virtual_memory()
            info["RAM_Total"] = f"{mem.total / (1024**3):.2f} GB"
            info["RAM_Available"] = f"{mem.available / (1024**3):.2f} GB"
        return info


    def confirm_and_start(self, op_name, n, mode, rand_count, sim_method, shots, is_all, ui_elements, exec_mode):
        if self.is_running:
            messagebox.showwarning("Warning", "A test is already running.")
            return

        try:
            shots = int(shots)
            if shots <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of shots must be a positive integer.")
            return

        base_tests = 2**(2*n)

        if mode == "Exhaustive":
            est_mem_bytes = base_tests * 64 
            if HAS_PSUTIL:
                mem = psutil.virtual_memory()
                if est_mem_bytes > (mem.available * 0.7):
                    est_gb = est_mem_bytes / (1024**3)
                    avail_gb = mem.available / (1024**3)
                    messagebox.showerror(
                        "Insufficient Memory for Exhaustive Test",
                        f"The Exhaustive test cannot be executed because generating the test cases exceeds available system memory.\n\n"
                        f"Estimated Test Cases: {base_tests:,}\n"
                        f"Estimated Memory Required: {est_gb:.2f} GB\n"
                        f"Available System Memory: {avail_gb:.2f} GB\n\n"
                        f"Suggestion: Please use 'Random Test' for large values of n."
                    )
                    return

        ops_to_run = list(self.logic.op_table.keys()) if is_all else [op_name]
        op_test_counts = {}

        if mode == "Exhaustive":
            for op in ops_to_run:
                op_test_counts[op] = base_tests
        else:
            if is_all:
                total_rand = min(rand_count, base_tests * len(ops_to_run))
                base_per_op = total_rand // len(ops_to_run)
                remainder = total_rand % len(ops_to_run)
                for op in ops_to_run:
                    if "1. Addition A+B" in op:
                        op_test_counts[op] = min(base_per_op + remainder, base_tests)
                    else:
                        op_test_counts[op] = min(base_per_op, base_tests)
            else:
                op_test_counts[ops_to_run[0]] = min(rand_count, base_tests)

        total_executions = sum(op_test_counts.values())

        if mode == "Random" and rand_count > (base_tests * len(ops_to_run)):
            messagebox.showinfo("Adjusted", f"Random tests requested exceeds maximum possible. Capped at {base_tests * len(ops_to_run)}.")

        hw = self.get_hardware_info()

        time_multiplier = 0.1

        if "statevector" in sim_method.lower():
            dummy_a = format(0, f'0{n}b')
            dummy_b = format(0, f'0{n}b')
            try:
                dummy_qc = self.logic.build_alu(ops_to_run[0], dummy_a, dummy_b)
                
                from Quantum_Processor import QuantumProcessor
                temp_processor = QuantumProcessor()
                dummy_qc = temp_processor.apply_execution_mode(dummy_qc, mode=exec_mode)
                
                num_qubits = dummy_qc.num_qubits

                est_sv_mem_bytes = 16 * (2 ** num_qubits)
                
                if HAS_PSUTIL:
                    mem = psutil.virtual_memory()
                    if est_sv_mem_bytes > mem.available:
                        est_gb = est_sv_mem_bytes / (1024**3)
                        avail_gb = mem.available / (1024**3)
                        messagebox.showerror(
                            "Insufficient Memory for Statevector",
                            f"The simulation cannot be executed because the machine does not have sufficient memory.\n\n"
                            f"Total Qubits in Circuit: {num_qubits}\n"
                            f"Estimated Statevector RAM: {est_gb:.2f} GB\n"
                            f"Available System RAM: {avail_gb:.2f} GB\n\n"
                            f"Suggestion: Please use the 'Matrix Product State (MPS)' simulator."
                        )
                        return
            except Exception:
                pass
        else:
            time_multiplier = 0.05  

        est_time_sec = total_executions * (n * time_multiplier)

        mode_names = {1: "No Transpilation", 2: "Standard (7T)", 3: "Custom (4T)"}
        mode_str = mode_names.get(exec_mode, "Unknown")

        msg = f"--- Test Estimation ---\n"
        msg += f"Operation(s): {len(ops_to_run)} selected\nMode: {mode}\nQubits: {n}\nTotal Circuits to run: {total_executions}\n"
        msg += f"Simulator: {sim_method} (Shots: {shots}) | Exec Mode: {mode_str}\n\n"
        msg += f"--- Hardware ---\nCPU: {hw['CPU']} ({hw['Cores']} cores)\nRAM Available: {hw['RAM_Available']}\n\n"
        msg += f"Estimated Time: {est_time_sec:.2f} seconds\n\nStart Simulation?"

        if messagebox.askyesno("Simulation Confirmation", msg):
            self.cancel_flag = False
            self.is_running = True
            ui_elements["start_btn"].config(state=tk.DISABLED)
            ui_elements["stop_btn"].config(state=tk.NORMAL)
            
            t = threading.Thread(
                target=self.run_test_loop,
                args=(ops_to_run, n, mode, op_test_counts, sim_method, shots, ui_elements, exec_mode)
            )
            t.daemon = True
            t.start()


    def cancel_test(self):
        if messagebox.askyesno("Cancel Test", "Are you sure you want to stop the current test?"):
            self.cancel_flag = True


    def calculate_classical_expected(self, op_name, A, B, n):
        mask = (1 << n) - 1
        mask_n_plus_1 = (1 << (n + 1)) - 1
        if op_name.startswith("1."): res = A + B
        elif op_name.startswith("2."): res = A + B + 1
        elif op_name.startswith("3."): res = A - B
        elif op_name.startswith("4."): res = B - A
        elif op_name.startswith("5."): res = ~(A + B)
        elif op_name.startswith("6."): res = A - B - 1
        elif op_name.startswith("7."): res = B - A - 1
        elif op_name.startswith("8."): res = (~A) + (~B)
        elif op_name.startswith("9."): res = A ^ B
        elif op_name.startswith("10."): res = ~(A ^ B)
        elif op_name.startswith("11."): res = A & B
        elif op_name.startswith("12."): res = A & (~B)
        elif op_name.startswith("13."): res = (~A) & B
        elif op_name.startswith("14."): res = (~A) & (~B)
        elif op_name.startswith("15."): res = (~A) | (~B)
        elif op_name.startswith("16."): res = A | (~B)
        elif op_name.startswith("17."): res = (~A) | B
        elif op_name.startswith("18."): res = A | B
        elif op_name.startswith("19."): return ((A ^ B) | (1 << n)) & mask_n_plus_1
        elif op_name.startswith("20."): return ((A ^ B ^ mask) | (1 << n)) & mask_n_plus_1
        else: res = 0
        return res & mask


    def get_op_symbol(self, op_name):
        name = op_name.lower()
        if "+" in name: return "+"
        if "-" in name: return "-"
        if "xnor" in name: return "⊙"
        if "xor" in name: return "⊕"
        if "and" in name: return "∧"
        if "or" in name: return "∨"
        return "Op"


    def run_test_loop(self, ops_to_run, n, mode, op_test_counts, sim_method, shots, ui, exec_mode):
        import gc 
        import time
        from datetime import datetime
        import random
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        import tkinter as tk

        from Quantum_Processor import QuantumProcessor
        processor = QuantumProcessor()

        log = ui["log"]
        prog = ui["progress"]
        total_executions = sum(op_test_counts.values())
        prog["maximum"] = total_executions
        prog["value"] = 0

        # --- NEW: Tunable batch limit for garbage collection ---
        gc_batch_size = 100 

        self.window.after(0, lambda: log.delete(1.0, tk.END))
        self.window.after(0, lambda: log.insert(tk.END, f"Starting {mode} Test on {n} qubits using {sim_method} (Shots: {shots})...\n\n"))

        if "statevector" in sim_method.lower():
            sim_backend = AerSimulator(method='statevector')
        else:
            sim_backend = AerSimulator(method='matrix_product_state')

        results = {
            "metadata": {
                "date": str(datetime.now()),
                "n_qubits": n,
                "mode": mode,
                "sim_method": sim_method,
                "shots": shots,
                "execution_mode": exec_mode,
                "hardware": self.get_hardware_info()
            },
            "operations": {}
        }

        start_time = time.time()
        global_count = 0
        global_passed = 0
        global_failed = 0

        for op_name in ops_to_run:
            if self.cancel_flag: break
            test_count = op_test_counts[op_name]
            if test_count == 0: continue

            is_carry_op = op_name.startswith("19.") or op_name.startswith("20.")
            expected_bit_len = n + 1 if is_carry_op else n

            op_stats = {"passed": 0, "failed": 0, "detailed_records": [], "failed_cases": []}
            symbol = self.get_op_symbol(op_name)
            cases = []

            if mode == "Exhaustive":
                for a in range(2**n):
                    for b in range(2**n):
                        cases.append((a, b))
            else:
                cases_set = set()
                while len(cases_set) < test_count:
                    cases_set.add((random.randint(0, 2**n - 1), random.randint(0, 2**n - 1)))
                cases = list(cases_set)

            for i, (A, B) in enumerate(cases):
                if self.cancel_flag: break
                
                a_bin = format(A, f'0{n}b')
                b_bin = format(B, f'0{n}b')
                expected_int = self.calculate_classical_expected(op_name, A, B, n)
                expected_bin = format(expected_int, f'0{expected_bit_len}b')

                status = ""
                q_res_val = ""
                counts_str = "{}"
                actual_method_used = "unknown"

                try:
                    qc = self.logic.build_alu(op_name, a_bin, b_bin)
                    
                    qc = processor.apply_execution_mode(qc, mode=exec_mode)
                    
                    job = sim_backend.run(qc, shots=int(shots))
                    job_result = job.result()

                    try:
                        actual_method_used = job_result.results[0].metadata.get('method', sim_method)
                    except Exception:
                        actual_method_used = sim_method

                    counts = job_result.get_counts()
                    counts_str = str(counts)
                    q_res = max(counts, key=counts.get)
                    q_res_val = q_res[-expected_bit_len:]  
                
                    if expected_bin == q_res_val:
                        op_stats["passed"] += 1
                        global_passed += 1
                        status = "PASS"
                    else:
                        op_stats["failed"] += 1
                        global_failed += 1
                        status = "FAIL"
                        op_stats["failed_cases"].append({
                            "A": A, "B": B, "Expected": expected_bin, "Quantum": q_res_val
                        })

                    del qc
                    del job
                    del job_result
                    
                    # --- NEW: Offloaded and batched garbage collection ---
                    if global_count % gc_batch_size == 0:
                        self.window.after(0, gc.collect)

                except Exception as e:
                    status = "ERROR"
                    q_res_val = f"ERR: {str(e)[:50]}"
                    op_stats["failed"] += 1
                    global_failed += 1

                record = {
                    "First_Number": a_bin,
                    "Second_Number": b_bin,
                    "Actual_Result": q_res_val,
                    "Expected_Result": expected_bin,
                    "Counts": counts_str,
                    "Method_Used": actual_method_used,
                    "Status": status
                }
                op_stats["detailed_records"].append(record)
                global_count += 1

                if global_count % 10 == 0 or global_count == total_executions or global_count == len(cases):
                    elapsed = time.time() - start_time
                    est_total = (elapsed / global_count) * total_executions
                    rem = est_total - elapsed
                    log_msg = f"[{op_name}] Case {i+1}/{test_count} | {a_bin} {symbol} {b_bin} = {q_res_val} | [{status}]\n"
                    log_msg += f"⚙️ Method: {actual_method_used} | 🎯 Counts: {counts_str}\n"
                    log_msg += f"✅ PASS: {op_stats['passed']}  | ❌ FAIL: {op_stats['failed']}\n"
                    
                    if len(ops_to_run) > 1:
                        log_msg += f"🌍 GLOBAL PASS: {global_passed}  | GLOBAL FAIL: {global_failed}\n"
                    
                    log_msg += f"⏱ Elapsed: {elapsed:.1f}s | Remaining: {rem:.1f}s"
                    self.window.after(0, lambda p=global_count, m=log_msg: self.update_ui_progress(prog, log, p, m))

            results["operations"][op_name] = op_stats

        elapsed_total = time.time() - start_time
        results["metadata"]["duration_seconds"] = elapsed_total
        ui["results_cache"] = results
        self.is_running = False
        self.cancel_flag = False

        final_msg = f"\n\n=== TEST COMPLETE ===\nTotal Time: {elapsed_total:.2f}s\n"
        if self.cancel_flag: final_msg = "\n\n=== TEST CANCELLED ===\n"
        self.window.after(0, lambda: log.insert(tk.END, final_msg))
        self.window.after(0, lambda: log.see(tk.END))
        self.window.after(0, lambda: ui["start_btn"].config(state=tk.NORMAL))
        self.window.after(0, lambda: ui["stop_btn"].config(state=tk.DISABLED))
        self.window.after(0, lambda: self.render_heatmaps(ui, n, ops_to_run, results))

    def update_ui_progress(self, prog, log, val, msg):
        prog["value"] = val
        log.delete("end-6l", tk.END) 
        log.insert(tk.END, "\n" + msg)
        log.see(tk.END)


    def render_heatmaps(self, ui, n, ops_run, results):
        if n >= 12:
            print(f"Skipping heatmap generation for n={n} to prevent memory overload.")
            messagebox.showinfo(
                "Visualization Skipped",
                f"For n={n}, a {2**n}x{2**n} matrix is too large for Matplotlib to render safely.\n\n"
                "Please use the 'Export JSON' or 'Export TXT' buttons to view your detailed results."
            )
            return

        is_all = ui.get("is_all", False)
        ui["figures"] = []  

        if not is_all:
            fig = ui["plot_fig"]
            canvas = ui["plot_canvas"]
            fig.clear()
            op_name = ops_run[0]
            short_name = op_name.split(". ")[1] if ". " in op_name else op_name
            op_data = results["operations"].get(op_name, {})
            grid_size = 2**n
            matrix = np.full((grid_size, grid_size), np.nan)

            for rec in op_data.get("detailed_records", []):
                try:
                    a_val = int(rec["First_Number"], 2)
                    b_val = int(rec["Second_Number"], 2)
                    r_val = int(rec["Actual_Result"], 2)
                    matrix[a_val, b_val] = r_val
                except ValueError:
                    continue

            ax = fig.add_subplot(111)
            im = ax.imshow(matrix, origin='lower', cmap='viridis', interpolation='nearest')
            cbar = fig.colorbar(im, ax=ax)
            cbar.ax.tick_params(labelsize=8)
            ax.set_title(f"{short_name}: Quantum Result R (n={n})", fontsize=11, fontweight='bold')
            ax.set_xlabel('B', fontsize=9)
            ax.set_ylabel('A', fontsize=9)
            ax.tick_params(labelsize=8)
            fig.tight_layout()
            canvas.draw()
            ui["figures"].append((short_name, fig))
        else:
            container = ui["plot_container"]
            for widget in container.winfo_children():
                widget.destroy()
            cols = 3
            for idx, op_name in enumerate(ops_run):
                row_idx = idx // cols
                col_idx = idx % cols
                card_frame = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")
                card_frame.grid(row=row_idx, column=col_idx, padx=8, pady=8)
                short_name = op_name.split(". ")[1] if ". " in op_name else op_name
                op_data = results["operations"].get(op_name, {})
                grid_size = 2**n
                matrix = np.full((grid_size, grid_size), np.nan)

                for rec in op_data.get("detailed_records", []):
                    try:
                        a_val = int(rec["First_Number"], 2)
                        b_val = int(rec["Second_Number"], 2)
                        r_val = int(rec["Actual_Result"], 2)
                        matrix[a_val, b_val] = r_val
                    except ValueError:
                        continue

                fig = Figure(figsize=(3.8, 2.8), dpi=85)
                ax = fig.add_subplot(111)
                im = ax.imshow(matrix, origin='lower', cmap='viridis', interpolation='nearest')
                cbar = fig.colorbar(im, ax=ax)
                cbar.ax.tick_params(labelsize=7)
                ax.set_title(f"{short_name} (n={n})", fontsize=9, fontweight='bold')
                ax.set_xlabel('B', fontsize=8)
                ax.set_ylabel('A', fontsize=8)
                ax.tick_params(labelsize=7)
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=card_frame)
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                canvas.draw()
                ui["figures"].append((short_name, fig))


    def export_results(self, fmt, ui_elements):
        data = ui_elements.get("results_cache", {})
        if not data:
            messagebox.showwarning("No Data", "No test results available to export. Run a test first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            initialfile=f"ALU_Test_Report.{fmt}"
        )
        if not path: return

        try:
            if fmt == "json":
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            elif fmt == "txt":
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("=== ALU TEST REPORT ===\n")
                    f.write(f"Date: {data['metadata']['date']}\n")
                    f.write(f"Simulation Method Selected: {data['metadata'].get('sim_method', 'N/A')}\n")
                    f.write(f"Shots: {data['metadata'].get('shots', 'N/A')}\n")
                    f.write(f"Duration: {data['metadata']['duration_seconds']:.2f}s\n\n")
                    for op, stats in data["operations"].items():
                        f.write(f"Op: {op} | Pass: {stats['passed']} | Fail: {stats['failed']}\n")
                        for rec in stats["detailed_records"]:
                            f.write(f"A:{rec['First_Number']}, B:{rec['Second_Number']}, Act:{rec['Actual_Result']}, Exp:{rec['Expected_Result']}, Status:{rec['Status']}, Counts:{rec['Counts']}, Method:{rec['Method_Used']}\n")
                        f.write("\n")
            elif fmt == "yaml":
                if HAS_YAML:
                    with open(path, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f)
                else:
                    messagebox.showerror("Error", "PyYAML is not installed. Please run 'pip install pyyaml'.")
                    return
            elif fmt == "xml":
                root = ET.Element("ALUTestReport")
                meta = ET.SubElement(root, "Metadata")
                for k, v in data["metadata"].items():
                    ET.SubElement(meta, k).text = str(v)
                ops = ET.SubElement(root, "Operations")
                for op_name, stats in data["operations"].items():
                    op_node = ET.SubElement(ops, "Operation", name=op_name)
                    ET.SubElement(op_node, "Passed").text = str(stats["passed"])
                    ET.SubElement(op_node, "Failed").text = str(stats["failed"])
                    details_node = ET.SubElement(op_node, "DetailedRecords")
                    for rec in stats["detailed_records"]:
                        rec_node = ET.SubElement(details_node, "Record")
                        for k, v in rec.items():
                            ET.SubElement(rec_node, k).text = str(v)
                tree = ET.ElementTree(root)
                tree.write(path, encoding="utf-8")
            
            messagebox.showinfo("Success", f"Successfully exported to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


    def save_heatmaps(self, ui_elements):
        import re
        import os
        
        figures = ui_elements.get("figures", [])
        if not figures:
            messagebox.showwarning("No Heatmaps", "No heatmaps available to save. Please run a test first to generate them.")
            return

        def sanitize_name(raw_name):

            clean = raw_name.replace(" ", "_").replace("+", "plus").replace("-", "minus")
            clean = clean.replace("|", "OR").replace("&", "AND").replace("~", "NOT").replace("^", "XOR")
            return re.sub(r'[^A-Za-z0-9_]', '', clean)

        if len(figures) == 1:
            name, fig = figures[0]
            safe_name = sanitize_name(name)
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=f"{safe_name}_Heatmap.png",
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
            )
            if path:
                try:
                    fig.savefig(path, bbox_inches='tight', dpi=300)
                    messagebox.showinfo("Success", f"Heatmap successfully saved to:\n{path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save image:\n{str(e)}")
        else:
            dir_path = filedialog.askdirectory(title="Select Directory to Save All Heatmaps")
            if dir_path:
                try:
                    for name, fig in figures:
                        safe_name = sanitize_name(name)
                        filepath = os.path.join(dir_path, f"{safe_name}_Heatmap.png")
                        fig.savefig(filepath, bbox_inches='tight', dpi=300)
                    messagebox.showinfo("Success", f"Successfully saved {len(figures)} heatmaps to:\n{dir_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save images:\n{str(e)}")