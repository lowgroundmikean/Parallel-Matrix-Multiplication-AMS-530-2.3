#!/usr/bin/env bash
#
# run23.slurm -- AMS 530 Project 2, Problem 2.3
#
# Sweeps N = 2^6, 2^8, 2^10, 2^12 over P = 1, 4, 8, 16.
# P = 1 is not part of the required table; it is the serial baseline T_1
# used for every speedup figure.
#
# All 16 ranks fit inside a single node, so no measurement in this sweep
# crosses the interconnect.  That is deliberate: it removes the node-boundary
# effect that dominated Project 1, and leaves the shape of the speedup curve
# determined by the algorithm rather than by rank placement.
#
# Submit with:   sbatch run23.slurm
#
#SBATCH --job-name=matmul23
#SBATCH --output=matmul23_%j.out
#SBATCH --error=matmul23_%j.err
#SBATCH --partition=short-96core
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00

set -u

module purge
module load openmpi/gcc12.1/4.1.4

cd "$SLURM_SUBMIT_DIR" || exit 1

echo "# job      : ${SLURM_JOB_ID:-none}"
echo "# partition: ${SLURM_JOB_PARTITION:-none}"
echo "# node      : $(hostname)"
echo "# cores     : $(nproc)"
echo "# date      : $(date)"
echo "# mpicc     : $(which mpicc)"
echo

# Build inside the job so the binary always matches the compute node's
# architecture, whatever the login node happens to be.
mpicc -O3 -funroll-loops -march=native -o matmul_mpi matmul_mpi.c -lm || {
    echo "build failed"; exit 1; }
echo "# build ok"
echo

for N in 64 256 1024 4096; do
    for P in 1 4 8 16; do
        echo "## N=$N P=$P"
        mpirun -np "$P" --bind-to core ./matmul_mpi "$N"
        echo
    done
done

echo "# sweep complete: $(date)"
