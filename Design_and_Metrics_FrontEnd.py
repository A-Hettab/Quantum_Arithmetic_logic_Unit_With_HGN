import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import json
import csv
import xml.etree.ElementTree as ET
import yaml

from Quantum_ALU_Logic import QALULogic
from Quantum_Processor import QuantumProcessor 
from Design_and_Metrics_BackEnd import Design_and_Metrics_PackEnd

class Design_and_Metrics_FrontEnd:

    def __init__(self, window):
        self.window = window
        self.window.title("⚛️ Design & Metrics")
        self.window.geometry("1400x1000") 
        self.window.configure(bg="#f0f0f0")

        self.logic = QALULogic()
        self.processor = QuantumProcessor() 

        self.funcs = Design_and_Metrics_PackEnd(self)

        self.full_a_entries = [] 
        self.full_b_entries = [] 
        self.all_ops_results = []

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TNotebook.Tab', font=('Helvetica', 10, 'bold'), padding=[8,4]) 
        self.style.configure('TLabel', font=('Helvetica', 11)) 

        settings_frame = tk.Frame(self.window, bg="#f0f0f0")
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Label(settings_frame, text="Simulation Method:", font=('Helvetica', 10, 'bold'), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)

        self.sim_method_var = tk.StringVar(value="matrix_product_state")
        self.sim_method_cb = ttk.Combobox(settings_frame, textvariable=self.sim_method_var,
                                         values=["matrix_product_state", "statevector"], 
                                         state="readonly", width=20)
        self.sim_method_cb.pack(side=tk.LEFT, padx=5)

        tk.Label(settings_frame, text="Shots:", font=('Helvetica', 10, 'bold'), bg="#f0f0f0").pack(side=tk.LEFT, padx=15)

        self.shots_var = tk.StringVar(value="1024")
        self.shots_entry = ttk.Entry(settings_frame, textvariable=self.shots_var, width=10)
        self.shots_entry.pack(side=tk.LEFT, padx=5)

        mode_frame = tk.LabelFrame(self.window, text="Execution Mode", font=('Helvetica', 10, 'bold'), bg="#f0f0f0", padx=10, pady=5)
        mode_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.exec_mode_var = tk.IntVar(value=3)

        tk.Radiobutton(mode_frame, text="High-Level Circuit (Mode 1)", 
                       variable=self.exec_mode_var, value=1, bg="#f0f0f0", font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(mode_frame, text="Standard Qiskit Decomposition (7-T Depth Toffoli/Fredkin)", 
                       variable=self.exec_mode_var, value=2, bg="#f0f0f0", font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(mode_frame, text="Relative Phase Optimization (4-T Depth Margolus Toffoli)", 
                       variable=self.exec_mode_var, value=3, bg="#f0f0f0", font=('Helvetica', 10)).pack(side=tk.LEFT, padx=10)

        ttk.Separator(self.window, orient='horizontal').pack(fill='x', pady=5)

        self.tabControl = ttk.Notebook(self.window)
        self.op_tabs = {} 

        for op_name in self.logic.op_table.keys():
            tab_frame = ttk.Frame(self.tabControl)
            short_name = op_name.split(". ")[1] if ". " in op_name else op_name
            self.tabControl.add(tab_frame, text=short_name)
            frame_alu = self.create_scrollable_tab(tab_frame)
            self.op_tabs[op_name] = frame_alu 
            self.setup_alu_tab(frame_alu, op_name)

        custom_tab_frame = ttk.Frame(self.tabControl)
        self.tabControl.add(custom_tab_frame, text="🔧 Custom Control")
        custom_frame_alu = self.create_scrollable_tab(custom_tab_frame)
        self.op_tabs["Custom Control"] = custom_frame_alu
        self.setup_custom_alu_tab(custom_frame_alu)

        self.tabControl.pack(expand=1, fill="both", pady=5)
        self.setup_return_button()

    def create_scrollable_tab(self, parent):
        container = tk.Frame(parent)
        canvas = tk.Canvas(container, bg="#f0f0f0", highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")
        window_id = canvas.create_window((0,0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=max(e.width, scrollable_frame.winfo_reqwidth())))

        container.pack(fill=tk.BOTH, expand=1)
        return scrollable_frame

    def setup_return_button(self):
        footer = tk.Frame(self.window, bg="#f0f0f0")
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        tk.Button(footer, text="⬅ Return to Main Menu", command=self.window.destroy,
                  bg="#d9534f", fg="white", font=("Helvetica", 10, "bold"), padx=20).pack(side=tk.RIGHT, padx=20)

    def setup_alu_tab(self, frame_alu, op_name):
        top_spec = tk.Frame(frame_alu)
        top_spec.pack(side=tk.TOP, fill=tk.X, pady=5) 

        entries_a = []
        entries_b = []

        def generate_inputs():
            for widget in frame_dynamic_inputs.winfo_children():
                widget.destroy()
            entries_a.clear()
            entries_b.clear() 
            n_val = int(entry_n.get())
            BITS_PER_ROW = 16 

            for i in range(n_val):
                row_offset = (i // BITS_PER_ROW) * 4
                col_index = i % BITS_PER_ROW
                bit_index = n_val - i - 1

                if col_index == 0:
                    tk.Label(frame_dynamic_inputs, text="Reg A", font=('Helvetica', 9, 'bold')).grid(row=row_offset+1, column=0, padx=5, sticky="e")
                    tk.Label(frame_dynamic_inputs, text="Reg B", font=('Helvetica', 9, 'bold')).grid(row=row_offset+2, column=0, padx=5, sticky="e")

                tk.Label(frame_dynamic_inputs, text=f"B{bit_index}", font=("Helvetica", 8)).grid(row=row_offset, column=col_index+1)

                e_a = tk.Entry(frame_dynamic_inputs, width=3, justify="center")
                e_a.insert(0,"0")
                e_a.grid(row=row_offset+1, column=col_index+1, padx=2, pady=2)
                entries_a.append(e_a)

                e_b = tk.Entry(frame_dynamic_inputs, width=3, justify="center")
                e_b.insert(0,"0")
                e_b.grid(row=row_offset+2, column=col_index+1, padx=2, pady=2)
                entries_b.append(e_b)

            total_rows = ((n_val - 1) // BITS_PER_ROW) * 4 + 4
            tk.Button(frame_dynamic_inputs, text=f"Run the QALU circuit ({op_name})", command=run_alu_op,
                      bg="#5bc0de", fg="white", font=("Helvetica", 10, "bold")).grid(row=total_rows, column=0, columnspan=BITS_PER_ROW+1, pady=15)

        def run_alu_op():
            try:
                a_bin = "".join([e.get().strip() if e.get().strip() in ['0','1'] else '0' for e in entries_a])
                b_bin = "".join([e.get().strip() if e.get().strip() in ['0','1'] else '0' for e in entries_b]) 

                qc = self.logic.build_alu(op_name, a_bin, b_bin) 
                n_val = int(entry_n.get())
                ctrl_str = self.logic.op_table[op_name]

                abstract_qc = self.funcs.build_abstract_visual_circuit(n_val, a_bin, b_bin, ctrl_str)
                selected_method = self.sim_method_var.get()
                selected_mode = self.exec_mode_var.get()  # FIXED: Retrieved execution mode

                try:
                    selected_shots = int(self.shots_var.get())
                except ValueError:
                    selected_shots = 1024 

                counts = self.processor.run_simulation(qc, method=selected_method, shots=selected_shots, mode=selected_mode)
                self.funcs.display_circuit_results(qc, abstract_qc, counts, circ_area, abstract_circ_area, hist_area, text_widget)

                res_bin = max(counts, key=counts.get)
                carry_bit = res_bin[0]
                                
                if "MSB=1" in op_name:
                    actual_result = res_bin        
                    decimal_val = int(res_bin, 2)  
                else:
                    actual_result = res_bin[1:]    
                    decimal_val = int(actual_result, 2)

                output_str = f"RESULT for {op_name}:\n"
                output_str += f"Total String: {res_bin} | Carry-Out: {carry_bit} | Final Result: {actual_result} (Decimal: {decimal_val})\n"
                output_str += "-"*40 + "\n" 
                text_widget.insert("1.0", output_str)

            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Label(top_spec, text="n (bits)").grid(row=0, column=0)
        entry_n = tk.Entry(top_spec, width=5)
        entry_n.insert(0, "4")
        entry_n.grid(row=0, column=1)
        tk.Button(top_spec, text="Generate Inputs", command=generate_inputs).grid(row=0, column=2, padx=5)

        frame_dynamic_inputs = tk.Frame(frame_alu)
        frame_dynamic_inputs.pack(fill=tk.X, pady=5) 

        circ_area = tk.Frame(frame_alu)
        circ_area.pack(fill=tk.BOTH, expand=1)
        abstract_circ_area = tk.Frame(frame_alu)
        abstract_circ_area.pack(fill=tk.BOTH, expand=1)
        hist_area = tk.Frame(frame_alu)
        hist_area.pack(fill=tk.BOTH, expand=1)
        text_widget = tk.Text(frame_alu, height=10)
        text_widget.pack(fill=tk.X)

        generate_inputs()

    def setup_custom_alu_tab(self, frame_alu):
        top_container = tk.Frame(frame_alu)
        top_container.pack(side=tk.TOP, fill=tk.X, pady=5)

        left_panel = tk.Frame(top_container)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        right_panel = tk.LabelFrame(top_container, text="📖 Control Sequence Guide & Batch Run", font=('Helvetica', 10, 'bold'), bg="#f8f9fa")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=5)

        op_lines = []
        for name, code in self.logic.op_table.items():
            if name == "Custom_Op":
                continue
            short_name = name.split(".")[1] if "." in name else name
            op_lines.append(f"{short_name:30}: {code}")

        guide_text = "\n".join(op_lines)
        guide_label = tk.Label(right_panel, text=guide_text, justify=tk.LEFT, font=('Consolas', 10), bg="#f8f9fa")
        guide_label.pack(padx=15, pady=5, anchor="w")

        btn_container = tk.Frame(right_panel, bg="#f8f9fa")
        btn_container.pack(pady=10)

        op_count = len([k for k in self.logic.op_table.keys() if k != "Custom_Op"])
        tk.Button(btn_container, text=f"🚀 Run All {op_count} Operations", command=self.funcs.run_all_operations, bg="#f0ad4e", fg="white", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)

        self.export_btn = tk.Button(btn_container, text="💾 Export Results", command=self.funcs.export_all_results, bg="#0275d8", fg="white", font=("Helvetica", 9, "bold"), state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.btn_export_table = tk.Button(btn_container, text="📑 Export Summary", command=self.funcs.export_summary, bg="#5cb85c", fg="white", font=("Helvetica", 9, "bold"), state=tk.DISABLED)
        self.btn_export_table.pack(side=tk.LEFT, padx=5)

        self.btn_visualize_charts = tk.Button(btn_container, text="📈 Visualize Charts", command=self.funcs.visualize_charts, bg="#17a2b8", fg="white", font=("Helvetica", 9, "bold"), state=tk.DISABLED)
        self.btn_visualize_charts.pack(side=tk.LEFT, padx=5)

        self.btn_visualize = tk.Button(btn_container, text="📊 Visualize Parameters", command=self.funcs.visualize_quantum_metrics, bg="#6c757d", fg="white", font=("Helvetica", 9, "bold"), state=tk.DISABLED)
        self.btn_visualize.pack(side=tk.LEFT, padx=5)

        top_spec = tk.Frame(left_panel)
        top_spec.pack(side=tk.TOP, fill=tk.X, pady=5)

        tk.Label(top_spec, text="n (bits)").grid(row=0, column=0, padx=5)
        self.entry_n = tk.Entry(top_spec, width=5)
        self.entry_n.insert(0, "4")
        self.entry_n.grid(row=0, column=1, padx=5)

        tk.Button(top_spec, text="Generate Inputs", command=self.generate_inputs).grid(row=0, column=2, padx=10)

        ctrl_frame = tk.Frame(left_panel)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(ctrl_frame, text="Control Qubits:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=10, rowspan=2)

        ctrl_labels = ["s0", "s1", "s2", "s3", "s4"]
        default_ctrls = ["0", "0", "0", "0", "0"]
        self.ctrl_entries = []

        for i, (label, default) in enumerate(zip(ctrl_labels, default_ctrls)):
            tk.Label(ctrl_frame, text=label).grid(row=0, column=i+1, padx=10)
            e = tk.Entry(ctrl_frame, width=3, justify="center")
            e.insert(0, default)
            e.grid(row=1, column=i+1, padx=10)
            self.ctrl_entries.append(e)

        self.entries_a = []
        self.entries_b = []

        self.frame_dynamic_inputs = tk.Frame(left_panel)
        self.frame_dynamic_inputs.pack(fill=tk.X, pady=5)

        self.circ_area = tk.Frame(frame_alu)
        self.circ_area.pack(fill=tk.BOTH, expand=1)

        self.abstract_circ_area = tk.Frame(frame_alu)
        self.abstract_circ_area.pack(fill=tk.BOTH, expand=1)

        self.hist_area = tk.Frame(frame_alu)
        self.hist_area.pack(fill=tk.BOTH, expand=1)

        self.text_widget = tk.Text(frame_alu, height=15)
        self.text_widget.pack(fill=tk.X)

        self.generate_inputs()

    def run_custom_alu(self):
        try:
            a_bin = "".join([e.get().strip() if e.get().strip() in ['0','1'] else '0' for e in self.entries_a])
            b_bin = "".join([e.get().strip() if e.get().strip() in ['0','1'] else '0' for e in self.entries_b])
            custom_ctrl_str = "".join([e.get().strip() for e in self.ctrl_entries if e.get().strip() in ['0','1']])

            if len(custom_ctrl_str) != 5:
                raise ValueError("You must enter exactly 5 control bits (0 or 1).")

            self.logic.op_table["Custom_Op"] = custom_ctrl_str
            qc = self.logic.build_alu("Custom_Op", a_bin, b_bin)
            n_val = int(self.entry_n.get())
            abstract_qc = self.funcs.build_abstract_visual_circuit(n_val, a_bin, b_bin, custom_ctrl_str)
            selected_method = self.sim_method_var.get()
            selected_mode = self.exec_mode_var.get()  # FIXED: Retrieved execution mode

            try:
                selected_shots = int(self.shots_var.get())
            except ValueError:
                selected_shots = 1024 

            counts = self.processor.run_simulation(qc, method=selected_method, shots=selected_shots, mode=selected_mode)
            self.funcs.display_circuit_results(qc, abstract_qc, counts, self.circ_area, self.abstract_circ_area, self.hist_area, self.text_widget)

            res_bin = max(counts, key=counts.get)
            carry_bit = res_bin[0]
                
            op_name = "Custom_Op"
            if "MSB=1" in op_name:
                actual_result = res_bin        
                decimal_val = int(res_bin, 2)  
            else:
                actual_result = res_bin[1:]    
                decimal_val = int(actual_result, 2)  

            output_str = f"RESULT for Custom Control [{custom_ctrl_str}]:\n"
            output_str += f"Total String: {res_bin} | Carry-Out: {carry_bit} | Final Result: {actual_result} (Decimal: {decimal_val})\n"
            output_str += "-"*40 + "\n"
            self.text_widget.insert("1.0", output_str)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def generate_inputs(self):
        for widget in self.frame_dynamic_inputs.winfo_children():
            widget.destroy()

        self.entries_a.clear()
        self.entries_b.clear()

        try:
            n_val = int(self.entry_n.get())
        except ValueError:
            n_val = 4

        BITS_PER_ROW = 16

        for i in range(n_val):
            row_offset = (i // BITS_PER_ROW) * 4
            col_index = i % BITS_PER_ROW
            bit_index = n_val - i - 1

            if col_index == 0:
                tk.Label(self.frame_dynamic_inputs, text="Reg A", font=('Helvetica', 9, 'bold')).grid(row=row_offset+1, column=0, padx=5, sticky="e")
                tk.Label(self.frame_dynamic_inputs, text="Reg B", font=('Helvetica', 9, 'bold')).grid(row=row_offset+2, column=0, padx=5, sticky="e")

            tk.Label(self.frame_dynamic_inputs, text=f"B{bit_index}", font=("Helvetica", 8)).grid(row=row_offset, column=col_index+1)

            e_a = tk.Entry(self.frame_dynamic_inputs, width=3, justify="center")
            e_a.insert(0,"0")
            e_a.grid(row=row_offset+1, column=col_index+1, padx=2, pady=2)
            self.entries_a.append(e_a)

            e_b = tk.Entry(self.frame_dynamic_inputs, width=3, justify="center")
            e_b.insert(0,"0")
            e_b.grid(row=row_offset+2, column=col_index+1, padx=2, pady=2)
            self.entries_b.append(e_b)

        total_rows = ((n_val - 1) // BITS_PER_ROW) * 4 + 4
        tk.Button(self.frame_dynamic_inputs, text="Run Custom ALU Operation", command=self.run_custom_alu,
                  bg="#5bc0de", fg="white", font=("Helvetica", 10, "bold")).grid(row=total_rows, column=0, columnspan=BITS_PER_ROW+1, pady=15)

if __name__ == "__main__":
    root = tk.Tk()
    app = Design_and_Metrics_FrontEnd(root)
    root.mainloop()