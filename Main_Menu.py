import tkinter as tk
from tkinter import ttk, messagebox
import sys

from Design_and_Metrics_FrontEnd import Design_and_Metrics_FrontEnd 
from Validation_and_Testing_FrontEnd import ValidationAndTestingFrontEnd 
from Run_IBM_Hardware_FrontEnd import QALUHardwareApp

class QuantumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚛️ Quantum Circuit Explorer")
        
        self.root.geometry("700x400") 
        self.root.configure(bg="#f5f5f5")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), background="#f5f5f5")
        style.configure("Menu.TButton", font=("Helvetica", 12), width=40) 
        style.configure("Danger.TButton", font=("Helvetica", 12, "bold"), foreground="white", background="#d9534f")

        ttk.Label(root, text="Quantum Research Dashboard", style="Header.TLabel").pack(pady=30)

        self.btn_frame = ttk.Frame(root)
        self.btn_frame.pack(expand=True, pady=10)

        ttk.Button(self.btn_frame, text="1. Design & Metrics", style="Menu.TButton",
                   command=self.open_our_proposal_alu).grid(row=0, column=0, pady=10)

        ttk.Button(self.btn_frame, text="2. Validation & Testing", style="Menu.TButton",
                   command=self.open_our_proposal_alu_test).grid(row=1, column=0, pady=10) 

        ttk.Button(self.btn_frame, text="3. IBM Quantum Hardware Execution", style="Menu.TButton",
                   command=self.open_ibm_hardware_menu).grid(row=2, column=0, pady=10)

        self.close_btn = tk.Button(root, text="❌ Close Application", 
                                   command=self.quit_app,
                                   bg="#d9534f", fg="white",
                                   font=("Helvetica", 11, "bold"),
                                   padx=20, pady=5)
        self.close_btn.pack(side=tk.BOTTOM, pady=20)


    def open_our_proposal_alu(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Our Proposal ALU Interface")
        new_window.geometry("850x650")
        Design_and_Metrics_FrontEnd(new_window)


    def open_our_proposal_alu_test(self):
        new_window = tk.Toplevel(self.root)
        ValidationAndTestingFrontEnd(new_window)


    def open_ibm_hardware_menu(self):
        new_window = tk.Toplevel(self.root)
        QALUHardwareApp(new_window)


    def quit_app(self):
        if messagebox.askokcancel("Quit", "Do you want to exit the entire application?"):
            self.root.destroy()
            sys.exit()


if __name__ == "__main__":
    root = tk.Tk()
    app = QuantumApp(root)
    root.mainloop()