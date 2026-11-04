from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

class QALULogic:

    def __init__(self):
        self._s0 = 0
        self._s1 = 1
        self._s2 = 2
        self._s3 = 3
        self._S4 = 4

        self.op_table = {
            "1. Addition: A + B": "00100",
            "2. Addition with Carry: A + B + 1": "00110",
            "3. Subtraction: A - B": "01110",
            "4. Reverse Subtraction: B - A": "10110",
            "5. Inverted Addition: NOT(A + B)": "11110",
            "6. Subtraction with Borrow: A - B - 1": "01100",
            "7. Reverse Subtraction with Borrow: B - A - 1": "10100",
            "8. NOT(A) + NOT(B)": "11100",
            "9. Bitwise XOR: A ⊕ B": "00000",
            "10. Bitwise XNOR: NOT(A ⊕ B)": "00010",
            "11. Bitwise AND: A ∧ B": "00001",
            "12. Bitwise AND: A AND NOT(B)": "01001",
            "13. Bitwise AND: NOT(A) AND B": "10001",
            "14. Bitwise AND: NOT(A) AND NOT(B)": "11001",
            "15. Bitwise NAND: NOT(A) OR NOT(B)": "11011", 
            "16. Bitwise OR: A OR NOT(B)": "01011",
            "17. Bitwise OR: NOT(A) OR B": "10011",
            "18. Bitwise OR: A ∨ B": "00011",
            "19. MSB=1 + XOR(A,B)": "10010",
            "20. MSB=1 + XNOR(A,B)": "11010"
        }

    def hgn_gate(self, qc, a, b, c, d):
        qc.ccx(a, b, d)
        qc.cx(a, b)
        qc.ccx(b, c, d)
        qc.cx(b, c)

    def apply_preprocessing(self, qc, reg_ctrl, reg_a, reg_b, reg_d, c_in, anc_c, n):
        qc.barrier(label="Control Preprocessing")
        for i in range(n):
            qc.cx(reg_ctrl[self._s0], reg_a[i])
            qc.cx(reg_ctrl[self._s1], reg_b[i])
            qc.cx(reg_ctrl[self._s3], anc_c[i])
            
        qc.cx(reg_ctrl[self._s3], c_in[0])

    def build_alu(self, op_name, a_binary, b_binary):
        n = len(a_binary)
        if op_name not in self.op_table:
            raise ValueError(f"Unknown operation: {op_name}")
        
        ctrl_vals = self.op_table[op_name]
        
        reg_a = QuantumRegister(n, 'a')       
        reg_b = QuantumRegister(n, 'b')       
        reg_d = QuantumRegister(n, 'd')       
        c_in = QuantumRegister(1, 'cin')      
        reg_ctrl = QuantumRegister(5, 'S')
        anc_c = QuantumRegister(n, 'anc_c')   
        creg = ClassicalRegister(n + 1, 'res') 
        
        qc = QuantumCircuit(reg_ctrl, reg_a, reg_b, c_in, reg_d, anc_c, creg)

        qc.barrier(label="Init Inputs")
        for i in range(n):
            if a_binary[-(i+1)] == '1': 
                qc.x(reg_a[i])
            if b_binary[-(i+1)] == '1': 
                qc.x(reg_b[i])
            
        for i in range(5):
            if ctrl_vals[i] == '1': 
                qc.x(reg_ctrl[i])

        self.apply_preprocessing(qc, reg_ctrl, reg_a, reg_b, reg_d, c_in, anc_c, n)

        qc.barrier(label="HGN Cascade & Optimized Multiplexing")
        
        c_wire = c_in[0] 
        measure_targets = []
        
        use_out_swap = (ctrl_vals[self._S4] == '1')
        use_carry_swap = (ctrl_vals[self._s2] == '1')


        for i in range(n):
            self.hgn_gate(qc, reg_a[i], reg_b[i], c_wire, reg_d[i])
            
            if use_out_swap:
                qc.swap(c_wire, reg_d[i])
            
            measure_targets.append(c_wire)
            
            if use_carry_swap:
                qc.swap(reg_d[i], anc_c[i])
            
            c_wire = anc_c[i]

        measure_targets.append(c_wire)

        qc.barrier(label="Measurement")
        for i in range(n + 1):
            qc.measure(measure_targets[i], creg[i])

        return qc

    def get_operations(self):
        return list(self.op_table.keys())