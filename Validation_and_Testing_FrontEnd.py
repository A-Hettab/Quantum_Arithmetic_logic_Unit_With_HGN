import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Validation_and_Testing_BackEnd import ValidationAndTestingPackEnd

from Quantum_ALU_Logic import QALULogic

class ValidationAndTestingFrontEnd(ValidationAndTestingPackEnd):

    def __init__(self, window):
        self.window = window
        self.window.title("⚛️ Validation & Testing - QALU Operations")
        self.window.geometry("1450x950")
        self.window.configure(bg="#f0f0f0")
        self.logic = QALULogic()
        self.is_running = False
        self.cancel_flag = False
        
        self.op_descriptions = {
            "1. Addition: A + B": "Performs standard binary addition (A + B).",
            "2. Addition with Carry: A + B + 1": "Performs binary addition with an initial carry of 1 (A + B + 1).",
            "3. Subtraction: A - B": "Performs two's complement subtraction (A - B).",
            "4. Reverse Subtraction: B - A": "Performs reversed two's complement subtraction (B - A).",
            "5. Inverted Addition: NOT(A + B)": "Computes the 1's complement of the sum (NOT(A + B)).",
            "6. Subtraction with Borrow: A - B - 1": "Performs subtraction missing a carry-in (borrow) (A - B - 1).",
            "7. Reverse Subtraction with Borrow: B - A - 1": "Performs reversed subtraction missing a carry-in (B - A - 1).",
            "8. NOT(A) + NOT(B)": "Adds the inverted values of A and B (NOT(A) + NOT(B)).",
            "9. Bitwise XOR: A ⊕ B": "Performs bitwise exclusive OR (A ⊕ B).",
            "10. Bitwise XNOR: NOT(A ⊕ B)": "Performs bitwise exclusive NOR (NOT(A ⊕ B)).",
            "11. Bitwise AND: A ∧ B": "Performs bitwise AND (A AND B).",
            "12. Bitwise AND: A AND NOT(B)": "Performs bitwise AND with inverted B (A AND NOT(B)).",
            "13. Bitwise AND: NOT(A) AND B": "Performs bitwise AND with inverted A (NOT(A) AND B).",
            "14. Bitwise AND: NOT(A) AND NOT(B)": "Performs bitwise AND on inverted inputs (NOT(A) AND NOT(B)).",
            "15. Bitwise NAND: NOT(A) OR NOT(B)": "Performs bitwise OR on inverted inputs (NOT(A) OR NOT(B)).",
            "16. Bitwise OR: A OR NOT(B)": "Performs bitwise OR with inverted B (A OR NOT(B)).",
            "17. Bitwise OR: NOT(A) OR B": "Performs bitwise OR with inverted A (NOT(A) OR B).",
            "18. Bitwise OR: A ∨ B": "Performs bitwise OR (A OR B).",
            "19. MSB=1 + XOR(A,B)": "Sets MSB to 1 and performs bitwise exclusive OR (MSB=1 + XOR(A,B)).",
            "20. MSB=1 + XNOR(A,B)": "Sets MSB to 1 and performs bitwise exclusive NOR (MSB=1 + XNOR(A,B)).",
            "All Operations": "Executes all 20 ALU operations sequentially to benchmark full system integrity."
        }
        
        self.setup_styles()
        self.build_gui()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TNotebook.Tab', font=('Helvetica', 10, 'bold'), padding=[10, 5])
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))

    def build_gui(self):
        self.tabControl = ttk.Notebook(self.window)
        for op_name, op_code in self.logic.op_table.items():
            tab_frame = ttk.Frame(self.tabControl)
            short_name = op_name.split(". ")[1] if ". " in op_name else op_name
            self.tabControl.add(tab_frame, text=short_name)
            self.build_test_tab(tab_frame, op_name, op_code, is_all=False)
            
        all_op_frame = ttk.Frame(self.tabControl)
        self.tabControl.add(all_op_frame, text="🌟 All Operations")
        self.build_test_tab(all_op_frame, "All Operations", "MIXED", is_all=True)
        
        footer = tk.Frame(self.window, bg="#f0f0f0")
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(
            footer, text="⬅ Return to Main Menu", command=self.window.destroy,
            bg="#d9534f", fg="white", font=("Helvetica", 10, "bold"), padx=20
        ).pack(side=tk.RIGHT, padx=20)
        
        self.tabControl.pack(expand=1, fill="both", pady=5)

    def build_test_tab(self, parent, op_name, op_code, is_all=False):
        ctrl_frame = tk.LabelFrame(parent, text=" Test Configuration ", font=('Helvetica', 10, 'bold'), bg="#f8f9fa")
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        desc_text = self.op_descriptions.get(op_name, "Operation logic test.")
        tk.Label(ctrl_frame, text=f"ℹ️ {desc_text}", bg="#f8f9fa", fg="#333", font=("Helvetica", 10, "italic")).grid(row=0, column=0, columnspan=6, sticky="w", padx=5, pady=2)
        
        tk.Label(ctrl_frame, text="Operand Bit-Width (n):", bg="#f8f9fa").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        n_var = tk.IntVar(value=4)
        n_entry = tk.Entry(ctrl_frame, textvariable=n_var, width=5)
        n_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        tk.Label(ctrl_frame, text="Total State Space (2²ⁿ): ", bg="#f8f9fa").grid(row=1, column=2, padx=10, sticky="w")
        max_test_label = tk.Label(ctrl_frame, text="...", font=('Helvetica', 10, 'bold'), bg="#f8f9fa", fg="#0275d8")
        max_test_label.grid(row=1, column=3, sticky="w")
        
        def update_max_tests(*args):
            try:
                n = n_var.get()
                base_tests = 2**(2*n)
                op_count = len(self.logic.op_table)
                total_tests = base_tests * op_count if is_all else base_tests
                max_test_label.config(text=f"{total_tests:,}")
            except Exception:
                max_test_label.config(text="N/A")
                
        n_var.trace_add("write", update_max_tests)
        update_max_tests()
        
        test_mode = tk.StringVar(value="Exhaustive")
        tk.Radiobutton(ctrl_frame, text="Exhaustive Test", variable=test_mode, value="Exhaustive", bg="#f8f9fa").grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        tk.Radiobutton(ctrl_frame, text="Random Test", variable=test_mode, value="Random", bg="#f8f9fa").grid(row=3, column=0, sticky="w", padx=5)
        rand_count_var = tk.IntVar(value=100)
        rand_entry = tk.Entry(ctrl_frame, textvariable=rand_count_var, width=10)
        rand_entry.grid(row=3, column=1, sticky="w")
        
        tk.Label(ctrl_frame, text="Qiskit Aer Backend:", bg="#f8f9fa", font=('Helvetica', 9, 'bold')).grid(row=1, column=4, padx=(20, 5), pady=2, sticky="e")
        sim_method_var = tk.StringVar(value="Matrix Product State (MPS)")
        sim_combo = ttk.Combobox(ctrl_frame, textvariable=sim_method_var, values=["Matrix Product State (MPS)", "Statevector"], state="readonly", width=25)
        sim_combo.grid(row=1, column=5, padx=5, pady=2, sticky="w")
        
        tk.Label(ctrl_frame, text="Number of Shots:", bg="#f8f9fa", font=('Helvetica', 9, 'bold')).grid(row=2, column=4, padx=(20, 5), pady=2, sticky="e")
        shots_var = tk.IntVar(value=1)
        shots_entry = tk.Entry(ctrl_frame, textvariable=shots_var, width=10)
        shots_entry.grid(row=2, column=5, padx=5, pady=2, sticky="w")
        
        info_code_lbl = tk.Label(ctrl_frame, text=f"Multiplexed Control Code (S0-S4): {op_code}", bg="#f8f9fa", fg="#5cb85c", font=("Helvetica", 9, "bold"))
        info_code_lbl.grid(row=3, column=4, columnspan=2, sticky="w", padx=(20, 5))

        tk.Label(ctrl_frame, text="Execution Mode:", bg="#f8f9fa", font=('Helvetica', 9, 'bold')).grid(row=1, column=6, padx=(20, 5), pady=2, sticky="e")
      
        exec_mode_var = tk.IntVar(value=1)
      
        tk.Radiobutton(ctrl_frame, text="High-Level Native Architecture (Direct HGN & Fredkin)", variable=exec_mode_var, value=1, bg="#f8f9fa").grid(row=1, column=7, sticky="w", padx=5)
      
        tk.Radiobutton(ctrl_frame, text="Standard Qiskit Decomposition (7-T Depth Toffoli/Fredkin)", variable=exec_mode_var, value=2, bg="#f8f9fa").grid(row=2, column=7, sticky="w", padx=5)
      
        tk.Radiobutton(ctrl_frame, text="Relative Phase Optimization (4-T Depth Margolus Toffoli)", variable=exec_mode_var, value=3, bg="#f8f9fa").grid(row=3, column=7, sticky="w", padx=5)

        ui_elements = {}
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=2)
        
        start_btn = tk.Button(
            btn_frame, text="▶ Start Test", bg="#5cb85c", fg="white", font=("Helvetica", 10, "bold"),
            command=lambda: self.confirm_and_start(
                op_name, n_var.get(), test_mode.get(), rand_count_var.get(),
                sim_method_var.get(), shots_var.get(), is_all, ui_elements, 
                exec_mode_var.get()
            )
        )
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = tk.Button(
            btn_frame, text="⏹ Cancel Test", bg="#d9534f", fg="white", font=("Helvetica", 10, "bold"),
            state=tk.DISABLED, command=self.cancel_test
        )
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        stats_frame = tk.LabelFrame(parent, text=" Test Execution & Progress ", font=('Helvetica', 10, 'bold'))
        stats_frame.pack(fill=tk.X, padx=10, pady=2)
        
        progress = ttk.Progressbar(stats_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        progress.pack(fill=tk.X, padx=10, pady=5)
        
        log_text = tk.Text(stats_frame, height=7, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)
        
        exp_frame = tk.Frame(parent)
        exp_frame.pack(fill=tk.X, padx=10, pady=2)
        
        tk.Button(exp_frame, text="💾 Export TXT", command=lambda: self.export_results("txt", ui_elements), width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(exp_frame, text="💾 Export JSON", command=lambda: self.export_results("json", ui_elements), width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(exp_frame, text="💾 Export XML", command=lambda: self.export_results("xml", ui_elements), width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(exp_frame, text="💾 Export YAML", command=lambda: self.export_results("yaml", ui_elements), width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(
            exp_frame, text="🖼️ Save Heatmap(s)", command=lambda: self.save_heatmaps(ui_elements),
            width=18, bg="#5bc0de", fg="black"
        ).pack(side=tk.LEFT, padx=10)
        
        plot_frame = tk.LabelFrame(parent, text=" Aer Heatmap Visualizations ", font=('Helvetica', 10, 'bold'))
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        if is_all:
            canvas_scroll = tk.Canvas(plot_frame, bg="#ffffff")
            scrollbar = ttk.Scrollbar(plot_frame, orient="vertical", command=canvas_scroll.yview)
            scrollable_container = ttk.Frame(canvas_scroll)
            scrollable_container.bind(
                "<Configure>",
                lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
            )
            canvas_scroll.create_window((0, 0), window=scrollable_container, anchor="nw")
            canvas_scroll.configure(yscrollcommand=scrollbar.set)
            canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            ui_elements["plot_container"] = scrollable_container
        else:
            fig = Figure(figsize=(6, 3.5), dpi=100)
            fig.subplots_adjust(bottom=0.2, left=0.15, right=0.9, top=0.85)
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            ui_elements["plot_fig"] = fig
            ui_elements["plot_canvas"] = canvas
            
        ui_elements.update({
            "start_btn": start_btn,
            "stop_btn": stop_btn,
            "progress": progress,
            "log": log_text,
            "results_cache": {},
            "is_all": is_all
        })