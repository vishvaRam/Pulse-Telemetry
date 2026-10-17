import ctypes
import os
import sys
import time

# 1. Dynamically locate the CUDA Driver library
if sys.platform.startswith("win"):
    cuda_lib_name = "nvcuda.dll"
else:
    cuda_lib_name = "libcuda.so.1"

try:
    cuda = ctypes.CDLL(cuda_lib_name)
except OSError:
    print(f"Error: Could not load '{cuda_lib_name}'. Ensure NVIDIA drivers are installed.")
    sys.exit(1)

# CUDA return type definitions
CUDA_SUCCESS = 0

# Initialize CUDA Driver API
res = cuda.cuInit(0)
if res != CUDA_SUCCESS:
    print(f"cuInit failed with error code: {res}")
    sys.exit(1)

# Get handle to first GPU
device = ctypes.c_int()
cuda.cuDeviceGet(ctypes.byref(device), 0)

# Create Context
context = ctypes.c_void_p()
cuda.cuCtxCreate_v2(ctypes.byref(context), 0, device)

# 2. Allocate Dedicated VRAM (e.g., 1.5 GB)
ALLOC_MB = 1500
ALLOC_BYTES = ALLOC_MB * 1024 * 1024

d_ptr = ctypes.c_ulonglong()
print(f"Allocating {ALLOC_MB} MB of VRAM...")
res = cuda.cuMemAlloc_v2(ctypes.byref(d_ptr), ctypes.c_size_t(ALLOC_BYTES))

if res != CUDA_SUCCESS:
    print(f"cuMemAlloc failed (Code {res}). Maybe requested too much memory?")
    cuda.cuCtxDestroy_v2(context)
    sys.exit(1)

print(f"Successfully allocated {ALLOC_MB} MB VRAM at device address: {hex(d_ptr.value)}")

# 3. Create host buffer to pump memory transfers (generates GPU engine core activity)
CHUNK_MB = 64
CHUNK_BYTES = CHUNK_MB * 1024 * 1024
host_buffer = (ctypes.c_char * CHUNK_BYTES)()

print("\n--- GPU Stress Active ---")
print("Check your monitoring dashboard now. Press Ctrl+C to terminate.")

try:
    while True:
        # Asynchronously blast host-to-device memory sets to saturate PCIe and GPU memory controllers
        # This keeps the 3D / Copy engines busy without needing custom compiled PTX kernels
        cuda.cuMemsetD8_v2(d_ptr, ctypes.c_ubyte(0xAA), ctypes.c_size_t(ALLOC_BYTES))
        cuda.cuCtxSynchronize()
        time.sleep(0.005)

except KeyboardInterrupt:
    print("\nStopping stress test and cleaning up VRAM...")

finally:
    # Free GPU memory and destroy context cleanly
    cuda.cuMemFree_v2(d_ptr)
    cuda.cuCtxDestroy_v2(context)
    print("VRAM released successfully.")