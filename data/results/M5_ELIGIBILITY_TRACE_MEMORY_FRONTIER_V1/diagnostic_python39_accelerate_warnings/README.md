# Runtime diagnostic output

This exploratory run used Python 3.9.6 / NumPy 2.0.2 linked to Apple Accelerate and emitted divide-by-zero, overflow, and invalid-operation warnings at matrix multiplication sites. All saved accuracy values were finite, but this output is retained only as a runtime diagnostic and excluded from the canonical result. The final experiment is rerun under Python 3.12 / NumPy 2.4.4.
