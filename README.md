# ⚛️ Quantum Circuit Explorer: QALU Research Dashboard

A comprehensive graphical interface for designing, validating, and testing Quantum Arithmetic Logic Unit (QALU) circuits. This tool provides an end-to-end pipeline from circuit design and metric evaluation to exhaustive simulation and real-world execution on IBM Quantum hardware.

## 🚀 Features

The application is unified under a central `MainMenu.py` dashboard, which provides access to three distinct modules:

### 1. Design & Metrics (`Design_and_Metrics_FrontEnd.py`)
*   **Execution Mode Selection:** Toggle between a High-Level Native Circuit, Standard Qiskit Decomposition (7-T Depth Toffoli/Fredkin), or Relative Phase Optimization (4-T Depth Margolus Toffoli) to analyze circuit depth and gate count trade-offs.
*   **Dynamic UI & Simulation Setup:** Dynamically generate binary input fields for Register A and Register B based on your specified operand bit-width ($n$). Configure backend simulation methods (`matrix_product_state` or `statevector`), set shot counts, and manually assign the 5-bit multiplexed control sequence ($s_0$-$s_4$).
*   **Circuit Generation & Visualization:** Generate and view a graphical circuit for each operation tailored to the chosen execution mode (1, 2, or 3). A separate, high-level abstract circuit is also drawn to illustrate HGN and Fredkin gates alongside their structural hierarchy. Automatically generate probability histograms for each operation, with built-in options to save both the circuit images and histograms locally.
*   **Operation-Specific Workspaces:** Navigate through a dedicated tab interface for each of the predefined QALU operations (Addition, Subtraction, Bitwise XOR, etc.), alongside a specialized "Custom Control" tab for testing experimental multiplexer configurations.
*   **Batch Processing & Analytics:** Run individual custom circuits or trigger a batch execution of all 20 QALU operations, and export raw data summaries and metrics.

### 2. Validation & Testing (`Validation_and_Testing_FrontEnd.py`)
*   **Test Configuration & Capabilities:** Test all 20 operations simultaneously or validate each operation separately. Users define operand bit-width ($n$), test mode (Exhaustive or Random), shot count, transpilation execution mode, and Qiskit Aer backend. **Simulation constraints are built-in: Matrix Product State (MPS) supports exhaustive testing up to $n=13$ and randomized testing for any $n$, while Statevector is restricted to $n \le 5$ for both exhaustive and randomized tests.** Includes pre-execution hardware profiling to estimate required RAM and block exhaustive simulations that exceed available system memory.
*   **Live Validation & Export:** Monitor real-time execution loops that automatically calculate the classical expected bitwise integer and compare it against the most frequent quantum result. Tracks global and operation-specific pass/fail rates, elapsed time, and raw state counts, with the ability to export full diagnostic reports to JSON, TXT, XML, or YAML.
*   **I/O Behavior Heatmaps:** Generate and save Matplotlib heatmaps that visually map the $2^n \times 2^n$ grid of Inputs A and B to the decoded Quantum Result R. Includes automated memory safeguards that bypass visual rendering for large qubit counts ($n \ge 12$) to prevent UI freezing.

### 3. IBM Quantum Hardware Execution (`Run_IBM_Hardware_FrontEnd.py`)
*   **Hardware Integration:** Connect directly to IBM Quantum backends using your secure API token.
*   **Job Management:** Submit your validated QALU circuits to real quantum processors, manage job queues, and monitor execution status.
*   **Empirical Analysis:** Retrieve and analyze physical hardware results, comparing real-world noise distributions and error rates against your ideal Aer simulator baselines.

## 🛠️ Prerequisites

*   **Python:** 3.11
*   **Qiskit:** 3.11.15
*   **Tkinter:** Included with standard Python installations
*   **IBM Quantum Account:** You will need an API token to run workloads on real hardware via the Execution module.

## 📥 Installation

1. **Clone or Download the repository:**
   *   **Option A (Clone via Git):**
       ```bash
       git clone [https://github.com/YourUsername/Quantum-Circuit-Explorer.git](https://github.com/YourUsername/Quantum-Circuit-Explorer.git)
       cd Quantum-Circuit-Explorer
       ```
   *   **Option B (Download ZIP):**
       Navigate to the repository page on GitHub, click the green **Code** button, and select **Download ZIP**. Extract the downloaded folder and open a terminal inside the extracted directory.

2. **Create a virtual environment (Recommended):**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`