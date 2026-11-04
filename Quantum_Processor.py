from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, transpile
import math

class QuantumProcessor:

    def __init__(self):
        self.simulator = AerSimulator()

    def apply_execution_mode(self, qc, mode=1):

        if mode == 1:
            return qc
            
        elif mode == 2:
            return transpile(qc, basis_gates=['cx', 'id', 'rz', 'sx', 'x'], optimization_level=3)
            
        elif mode == 3:
            custom_qc = QuantumCircuit(*qc.qregs, *qc.cregs)

            for instr, qargs, cargs in qc.data:
                if instr.name == 'ccx':
                    ctrl1, ctrl2, tgt = qargs
                    
                    custom_qc.h(tgt)
                    custom_qc.t(tgt)
                    custom_qc.cx(ctrl2, tgt)
                    custom_qc.tdg(tgt)
                    custom_qc.cx(ctrl1, tgt)
                    custom_qc.t(tgt)
                    custom_qc.cx(ctrl2, tgt)
                    custom_qc.tdg(tgt)
                    custom_qc.h(tgt)
                    
                elif instr.name == 'cswap':
                    ctrl, tgt1, tgt2 = qargs
                    
                    custom_qc.cx(tgt1, tgt2)
                    custom_qc.h(tgt1)
                    custom_qc.t(tgt1)
                    custom_qc.cx(ctrl, tgt1)
                    custom_qc.tdg(tgt1)
                    custom_qc.cx(tgt2, tgt1)
                    custom_qc.t(tgt1)
                    custom_qc.cx(ctrl, tgt1)
                    custom_qc.tdg(tgt1)
                    custom_qc.h(tgt1)
                    custom_qc.cx(tgt1, tgt2)
                    
                else:
                    custom_qc.append(instr, qargs, cargs)

            return transpile(custom_qc, basis_gates=['cx', 'id', 'rz', 'sx', 'x'], optimization_level=3)
            
        else:
            raise ValueError("Invalid mode selected. Please choose 1, 2, or 3.")

    def run_simulation(self, qc, method="matrix_product_state", shots=1024, mode=1):
        processed_qc = self.apply_execution_mode(qc, mode)
        job = self.simulator.run(processed_qc, shots=shots, method=method)
        return job.result().get_counts()

    def analyze_circuit(self, qc):
        return {
            "qubits": qc.num_qubits,
            "depth": qc.depth(),
            "gates": qc.size(),
            "operations": qc.count_ops()
        }

    def compute_metrics(self, qc, mode=1):
        cost_table = {
            "cx": 1, "ccx": 2, "cswap": 4, "swap": 3,
            "x": 1, "sx": 1, "rz": 0, "id": 0, "measure": 0, "barrier": 0
        }

        if mode in [2, 3]:
            transpiled_circuit = self.apply_execution_mode(qc, mode)
            ops = transpiled_circuit.count_ops()
            
            cx_count = ops.get("cx", 0)
            depth = transpiled_circuit.depth()
            qubits = transpiled_circuit.num_qubits - (transpiled_circuit.num_clbits if transpiled_circuit.num_clbits else 0)
            
            qc_cost = sum(cost_table.get(op, 1) * count for op, count in ops.items())
            
            t_count = ops.get("t", 0) + ops.get("tdg", 0)
            for instr, _, _ in transpiled_circuit.data:
                if instr.name == 'rz':
                    angle = float(instr.params[0])
                    normalized_k = angle / (math.pi / 4)
                    if abs(normalized_k - round(normalized_k)) < 1e-5 and round(normalized_k) % 2 != 0:
                        t_count += 1
                        
            return {
                "QC (Quantum Cost)": qc_cost,
                "QD (Depth)": depth,
                "QG (Qubits)": qubits,
                "T-count": t_count,
                "CX-count": cx_count
            }
            
        else:
            ops = qc.count_ops()
            qc_cost = sum(cost_table.get(op, 1) * count for op, count in ops.items())
            
            literal_t = ops.get('t', 0) + ops.get('tdg', 0)
            has_abstract_gates = 'ccx' in ops or 'cswap' in ops

            if has_abstract_gates:
                t_factor = 4 
                ccx_t_cost = ops.get('ccx', 0) * t_factor
                cswap_t_cost = ops.get('cswap', 0) * t_factor
                total_t_count = literal_t + ccx_t_cost + cswap_t_cost
            else:
                t_from_rz = 0
                for instr, _, _ in qc.data:
                    if instr.name == 'rz':
                        angle = float(instr.params[0])
                        normalized_k = angle / (math.pi / 4)
                        if abs(normalized_k - round(normalized_k)) < 1e-5 and round(normalized_k) % 2 != 0:
                            t_from_rz += 1
                total_t_count = literal_t + t_from_rz

            return {
                "QC (Quantum Cost)": qc_cost,
                "QD (Depth)": qc.depth(),
                "QG (Qubits)": qc.num_qubits - (qc.num_clbits if qc.num_clbits else 0),
                "T-count": total_t_count,
                "CX-count": ops.get("cx", 0)
            }