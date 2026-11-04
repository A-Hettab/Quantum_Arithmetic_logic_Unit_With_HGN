import os
import json
import math
import time
from datetime import datetime
from typing import Generator, Dict, Any, Tuple, Optional, List, Iterable

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from Quantum_ALU_Logic import QALULogic
from Quantum_Processor import QuantumProcessor

MIN_N = 1
MAX_N = 12
DEFAULT_SHOTS = 1024
DEFAULT_CHANNEL = "ibm_quantum_platform"
DEFAULT_OPTIMIZATION_LEVEL = 3
DEFAULT_BATCH_SIZE = 100
DEFAULT_OUTPUT_DIRECTORY = "ibm_results"

MODE_DESCRIPTIONS = {
    2: "Standard CCX / 7T-equivalent Toffoli",
    3: "4T Margolus Relative-Phase Toffoli"
}

class IBMHardwareRunner:
    def calculate_workload(self, n: int, shots: int = DEFAULT_SHOTS) -> Dict[str, int]:
        n = int(n)
        shots = int(shots)

        if not (MIN_N <= n <= MAX_N):
            raise ValueError(f"n must be between {MIN_N} and {MAX_N}.")
        if shots <= 0:
            raise ValueError("Shots must be greater than zero.")

        values_per_operand = 2 ** n
        input_pairs = values_per_operand ** 2
        number_operations = 20
        total_circuits = number_operations * input_pairs
        required_qubits = 4 * n + 6
        total_shots = total_circuits * shots

        return {
            "n": n,
            "number_operations": number_operations,
            "values_per_operand": values_per_operand,
            "input_pairs": input_pairs,
            "total_circuits": total_circuits,
            "shots_per_circuit": shots,
            "total_shots": total_shots,
            "required_qubits": required_qubits
        }

    def validate_mode(self, mode: int) -> int:
        mode = int(mode)
        if mode not in MODE_DESCRIPTIONS:
            raise ValueError(f"Mode must be one of {list(MODE_DESCRIPTIONS.keys())}.")
        return mode

    def generate_input_combinations(self, n: int) -> Generator[Tuple[str, str], None, None]:
        max_value = 2 ** n
        for a in range(max_value):
            for b in range(max_value):
                yield format(a, f"0{n}b"), format(b, f"0{n}b")

    def generate_all_circuits(
        self, alu: Any, operations: List[str], n: int, mode: int
    ) -> Generator[Tuple[Any, Dict[str, str]], None, None]:
        for operation in operations:
            for a_bin, b_bin in self.generate_input_combinations(n):
                
                processor = QuantumProcessor()

                qc = alu.build_alu(operation, a_bin, b_bin)

                processed_qc = processor.apply_execution_mode(qc, mode=mode)

                final_qc = processed_qc if processed_qc is not None else qc

                yield final_qc, {
                    "operation": operation,
                    "input_a": a_bin,
                    "input_b": b_bin
                }

    def batch_generator(
        self, iterable: Iterable[Tuple[Any, Dict[str, str]]], 
        batch_size: int
    ) -> Generator[Tuple[List[Any], List[Dict[str, str]]], None, None]:
        """Batches an iterable into chunks of size `batch_size`."""
        batch_circuits, batch_metadata = [], []
        for circuit, meta in iterable:
            batch_circuits.append(circuit)
            batch_metadata.append(meta)
            if len(batch_circuits) >= batch_size:
                yield batch_circuits, batch_metadata
                batch_circuits, batch_metadata = [], []
        if batch_circuits:
            yield batch_circuits, batch_metadata

    def extract_counts(self, pub_result: Any) -> Dict[str, int]:
        try:
            return dict(pub_result.data.res.get_counts())
        except AttributeError:
            pass

        data = pub_result.data
        for register_name in dir(data):
            if register_name.startswith("_"):
                continue
            try:
                register_data = getattr(data, register_name)
                if hasattr(register_data, "get_counts"):
                    return dict(register_data.get_counts())
            except Exception:
                continue

        raise RuntimeError("Unable to extract measurement counts from SamplerV2 result.")

    def analyze_counts(self, counts: Dict[str, int]) -> Dict[str, Any]:
        if not counts:
            return {"top_bitstring": None, "top_count": 0, "top_probability": 0.0}

        top_bitstring = max(counts, key=counts.get)
        top_count = counts[top_bitstring]
        total = sum(counts.values())
        probability = top_count / total if total > 0 else 0.0

        return {
            "top_bitstring": top_bitstring,
            "top_count": top_count,
            "top_probability": probability
        }

    def create_output_directory(self, output_directory: str) -> None:
        os.makedirs(output_directory, exist_ok=True)

    def _write_json_section(self, file_handle, key: str, data: Any) -> None:
        formatted = json.dumps(data, indent=2).replace("\n", "\n  ")
        file_handle.write(f'  "{key}": {formatted},\n')

    def _execute_batch(
        self,
        backend: Any,
        circuits: List[Any],
        metadata: List[Dict[str, str]],
        shots: int,
        optimization_level: int
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        print(f"  Transpiling for IBM hardware (optimization level {optimization_level})...")
        isa_circuits = transpile(circuits, backend=backend, optimization_level=optimization_level)
        print("  Transpilation completed.")

        sampler = Sampler(mode=backend)
        sampler.options.default_shots = shots
        
        print("  Submitting batch to IBM hardware...")
        batch_start_time = time.time()
        job = sampler.run(isa_circuits)
        job_id = job.job_id()
        print(f"  Job ID: {job_id}\n  Waiting for hardware result...")
        
        result = job.result()
        batch_end_time = time.time()
        batch_execution_time = batch_end_time - batch_start_time
        print(f"  Hardware execution completed in {batch_execution_time:.2f} seconds.")

        batch_records = []
        for local_index, pub_result in enumerate(result):
            counts = self.extract_counts(pub_result)
            analysis = self.analyze_counts(counts)
            meta = metadata[local_index]
            
            # Extract transpiled circuit metrics
            transpiled_qc = isa_circuits[local_index]
            depth = transpiled_qc.depth()
            ops = dict(transpiled_qc.count_ops())
            
            batch_records.append({
                "operation": meta["operation"],
                "input_a": meta["input_a"],
                "input_b": meta["input_b"],
                "raw_counts": counts,
                "top_bitstring": analysis["top_bitstring"],
                "top_count": analysis["top_count"],
                "top_probability": analysis["top_probability"],
                "transpilation_metrics": {
                    "depth": depth,
                    "gate_counts": ops
                }
            })

        return job_id, batch_records, batch_execution_time

    def run_ibm_exhaustive(
        self,
        token: str,
        n: int,
        mode: int,
        shots: int = DEFAULT_SHOTS,
        channel: str = DEFAULT_CHANNEL,
        backend_name: Optional[str] = None,
        output_directory: str = DEFAULT_OUTPUT_DIRECTORY,
        save_results: bool = True,
        batch_size: int = DEFAULT_BATCH_SIZE,
        optimization_level: int = DEFAULT_OPTIMIZATION_LEVEL
    ) -> Dict[str, Any]:
        
        n = int(n)
        shots = int(shots)
        mode = self.validate_mode(mode)

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        workload = self.calculate_workload(n, shots)
        total_circuits = workload["total_circuits"]
        experiment_start = datetime.now()

        print("\n" + "=" * 70)
        print("QALU IBM QUANTUM HARDWARE EXHAUSTIVE TEST")
        print("=" * 70)
        print(f"n                         : {n}")
        print(f"Mode                      : {mode}")
        print(f"Mode description          : {MODE_DESCRIPTIONS[mode]}")
        print(f"Operations                : {workload['number_operations']}")
        print(f"Input pairs               : {workload['input_pairs']:,}")
        print(f"Total circuits            : {total_circuits:,}")
        print(f"Shots per circuit         : {shots:,}")
        print(f"Total shots               : {workload['total_shots']:,}")
        print(f"Required QALU qubits      : {workload['required_qubits']}")
        print(f"Optimization level        : {optimization_level}")
        print(f"Batch size                : {batch_size}")
        print("\nError mitigation: OFF for all (M3, Readout, DD, Twirling)")
        print("=" * 70)

        if save_results:
            self.create_output_directory(output_directory)

        print("\n[1] Connecting to IBM Quantum...")
        try:
            service = QiskitRuntimeService(channel=channel, token=token, instance="ibm-q/open/main")
        except Exception:
            service = QiskitRuntimeService(channel=channel, token=token)
        print("    Successfully connected.\n")
        
        print("[2] Selecting real IBM quantum backend...")
        if backend_name:
            print(f"    Requested backend: {backend_name}")
            backend = service.backend(backend_name)
            if not backend.operational:
                raise RuntimeError(f"Backend '{backend_name}' is not operational.")
            if backend.num_qubits < workload["required_qubits"]:
                raise RuntimeError(f"Backend '{backend_name}' has {backend.num_qubits} qubits, but required: {workload['required_qubits']}.")
        else:
            backend = service.least_busy(
                operational=True,
                simulator=False,
                min_num_qubits=workload["required_qubits"]
            )
        print(f"    Selected backend: {backend.name}")
        print(f"    Backend qubits: {backend.num_qubits}")

        alu = QALULogic()
        operations = alu.get_operations()
        timestamp = experiment_start.strftime("%Y%m%d_%H%M%S")
        output_filename = f"qalu_n{n}_mode{mode}_{backend.name}_{timestamp}.json"
        output_path = os.path.join(output_directory, output_filename)

        experiment_data = {
            "experiment": {
                "name": "QALU Exhaustive IBM Hardware Test",
                "n": n,
                "operations": len(operations),
                "input_pairs": workload["input_pairs"],
                "total_circuits": total_circuits,
                "shots_per_circuit": shots,
                "total_shots": workload["total_shots"],
                "required_qubits": workload["required_qubits"]
            },
            "implementation": {
                "mode": mode,
                "mode_description": MODE_DESCRIPTIONS[mode],
                "optimization_level": optimization_level
            },
            "error_mitigation": {
                "m3": False,
                "readout_mitigation": False,
                "dynamical_decoupling": False,
                "gate_twirling": False,
                "measurement_twirling": False
            },
            "hardware": {
                "backend": backend.name,
                "num_qubits": backend.num_qubits,
                "channel": channel
            },
            "execution": {
                "job_ids": [],
                "job_execution_times_seconds": [],
                "number_of_jobs": 0,
                "batch_size": batch_size,
                "start_time": experiment_start.isoformat(),
                "end_time": None,
                "total_execution_time_seconds": None
            },
            "results": []
        }

        output_file_handle = None
        if save_results:
            output_file_handle = open(output_path, "w", encoding="utf-8")
            output_file_handle.write("{\n")
            self._write_json_section(output_file_handle, "experiment", experiment_data["experiment"])
            self._write_json_section(output_file_handle, "implementation", experiment_data["implementation"])
            self._write_json_section(output_file_handle, "error_mitigation", experiment_data["error_mitigation"])
            self._write_json_section(output_file_handle, "hardware", experiment_data["hardware"])
            self._write_json_section(output_file_handle, "execution", experiment_data["execution"])
            output_file_handle.write('  "results": [\n')

        circuit_gen = self.generate_all_circuits(alu, operations, n, mode)
        batches = self.batch_generator(circuit_gen, batch_size)
        
        total_batches = math.ceil(total_circuits / batch_size)
        global_circuit_index = 0
        first_result = True
        batch_number = 0

        try:
            for batch_circuits, batch_metadata in batches:
                batch_number += 1
                print("\n" + "-" * 70)
                print(f"Batch {batch_number}/{total_batches} (Logical circuits: {len(batch_circuits)})")

                job_id, records, batch_exec_time = self._execute_batch(
                    backend=backend,
                    circuits=batch_circuits,
                    metadata=batch_metadata,
                    shots=shots,
                    optimization_level=optimization_level
                )
                experiment_data["execution"]["job_ids"].append(job_id)
                experiment_data["execution"]["job_execution_times_seconds"].append(batch_exec_time)

                for record in records:
                    global_circuit_index += 1
                    record["circuit_index"] = global_circuit_index
                    record["batch_index"] = batch_number

                    if output_file_handle:
                        if not first_result:
                            output_file_handle.write(",\n")
                        formatted_record = json.dumps(record, indent=4)
                        indented_record = "\n".join("    " + line for line in formatted_record.splitlines())
                        output_file_handle.write(indented_record)
                        output_file_handle.flush()
                        first_result = False

                    if global_circuit_index == 1 or global_circuit_index % 50 == 0:
                        print(f"    Processed circuits: {global_circuit_index:,}")
                
                if global_circuit_index % 50 != 0:
                    print(f"    Processed circuits: {global_circuit_index:,}")

        finally:
            experiment_end = datetime.now()
            experiment_data["execution"]["end_time"] = experiment_end.isoformat()
            experiment_data["execution"]["total_execution_time_seconds"] = (experiment_end - experiment_start).total_seconds()
            experiment_data["execution"]["number_of_jobs"] = len(experiment_data["execution"]["job_ids"])
            
            if output_file_handle:
                output_file_handle.write("\n  ]\n}\n")
                output_file_handle.close()

        experiment_data["output_file"] = output_path if save_results else None

        print("\n" + "=" * 70)
        print("EXECUTION COMPLETED")
        print("=" * 70)
        print(f"Circuits executed : {global_circuit_index:,}")
        print(f"IBM jobs          : {experiment_data['execution']['number_of_jobs']}")
        print(f"Total exec time   : {experiment_data['execution']['total_execution_time_seconds']:.2f} seconds")
        print(f"Backend           : {backend.name}")
        if save_results:
            print(f"Results saved to  : {output_path}")
        print("=" * 70)

        return experiment_data

if __name__ == "__main__":
    print("This module is intended to be called from Run_IBM_Hardware_FrontEnd.py.")
    print("To execute an experiment, instantiate the class and call the method:")
    print("runner = IBMHardwareRunner()")
    print("runner.run_ibm_exhaustive(...)")