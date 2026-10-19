# Parallel Dense Matrix Multiplication in MPI
 
A row-wise distributed matrix multiply, benchmarked across
N ∈ {2⁶, 2⁸, 2¹⁰, 2¹²} and P ∈ {2², 2³, 2⁴} on a 28-core dual-socket
Haswell node, with an analysis of why the speedup curve bends where it does.
 
**The short version.** The speedup figures are unremarkable: 10.21× on sixteen
ranks at N = 4096. What is interesting is the N = 1024 row, where speedup
*falls* going from eight ranks to sixteen, and compute time rises in absolute
terms even though each rank's arithmetic has been halved. That is not
communication, not scheduler contention, and not noise. It reproduced exactly
on two separate nodes under exclusive allocation.
 
The cause is the design decision itself. Every rank holds a private copy of
**B**, so aggregate last-level cache demand grows as P·N². Per-rank throughput
collapses by a factor of 2.5 precisely where that demand crosses the 35 MiB
physical L3:
 
| N | P | L3 demanded per socket | ÷ 35 MiB | GFLOP/s per rank |
|---|---|---|---|---|
| 1024 | 4 | 24.0 MiB | 0.69 | 6.38 |
| 1024 | 8 | 40.0 MiB | 1.14 | 4.89 |
| 1024 | 16 | 72.0 MiB | **2.06** | **1.97** |
 
One mechanism, no fitted parameters, and it also explains why N = 256 scales
cleanly (never exceeds 13% of capacity) and why N = 4096 degrades gradually
rather than abruptly (never fit at any P, so there was no residency to lose).
 
Full derivation, methodology and the Amdahl discussion are in my report.
 
---
 
## Results
 
Wall-clock seconds, speedup in parentheses, relative to a dedicated P = 1 run.
 
| N | P = 4 | P = 8 | P = 16 |
|---|---|---|---|
| 2⁶ | 0.000077 (1.26×) | 0.000100 (0.97×) | 0.000120 (0.81×) |
| 2⁸ | 0.002400 (3.15×) | 0.001606 (4.70×) | 0.001605 (4.71×) |
| 2¹⁰ | 0.115582 (2.80×) | 0.072050 (4.50×) | 0.079955 (4.05×) |
| 2¹² | 12.550124 (4.05×) | 6.875919 (7.39×) | 4.976300 (10.21×) |
 
All sixteen configurations verify against the serial baseline at **exactly zero
relative error**. This is structural rather than lucky: the row-wise
decomposition assigns each output element entirely to one rank and preserves
the order of the k-summation, so no floating-point reassociation occurs and the
parallel and serial results are bit-identical. Any non-zero residual therefore
indicates a genuine indexing bug, not accumulated rounding — a sharper test
than a tolerance comparison.
 
### On Amdahl's law
 
The Karp-Flatt metric, which inverts measured speedup to recover the serial
fraction Amdahl's law would require, falls by two orders of magnitude across
the sweep:
 
| N | e(P=4) | e(P=8) | e(P=16) | implied ceiling 1/e |
|---|---|---|---|---|
| 2⁶ | 0.7251 | 1.0353 | 1.2529 | 1.4× |
| 2⁸ | 0.0903 | 0.1001 | 0.1600 | 11.1× |
| 2¹⁰ | 0.1424 | 0.1113 | 0.1966 | 9.0× |
| 2¹² | −0.0041 | 0.0118 | 0.0378 | — |
 
There is no fixed serial fraction here. What resists parallelisation is
communication, scaling as βN² against arithmetic scaling as cN³/P, so
f_eff ≈ β/(cN) is a function of problem size. Within each row, e nonetheless
*rises* with P even at N = 2¹² where communication never exceeds 5.5% of wall
time — and that residual is the cache effect above, for which Amdahl's model
has no term.
 
---
 
## Algorithm
 
One-dimensional row-wise block decomposition:
 
- **A** partitioned by rows, N/P rows per rank
- **B** replicated in full on every rank
- **C** distributed like A, gathered on the root
Three collectives carry all traffic — `MPI_Scatter`, `MPI_Bcast`, `MPI_Gather` —
and the computation between them is dependency-free, so the program contains no
point-to-point messaging and no deadlock or race by construction.
 
**Why not Cannon or SUMMA?** They are asymptotically better, moving 2N²/√P per
rank against this scheme's N². But they require a √P × √P square process grid,
and the assignment mandates P = 8. **√8 is not an integer.** Any 2D scheme would
have to degrade to a 2×4 rectangular grid at exactly one of the three required
data points, so the middle column of every table would describe a different
algorithm from the columns beside it. Uniformity across the sweep was judged
worth a factor of √P/2 in communication volume, which at P = 16 is a factor of
two.
 
Trade-offs, stated plainly:
 
| | this scheme | Cannon |
|---|---|---|
| Per-rank communication | N² | 2N²/√P |
| Per-rank memory | Θ(N²) | Θ(N²/P) |
| Isoefficiency | Θ(P³) | Θ(P^{3/2}) |
| Works at P = 8 | yes | no |
 
The Θ(N²) per-rank memory is the line that matters. The conventional
expectation is that it bites as an allocation failure at large N; the
measurements show it biting far earlier and far more quietly, as a cache
capacity effect at a problem size that sits comfortably in DRAM.
 
---
 
## Layout
 
```
.
├── matmul_mpi.c                      # the MPI implementation
├── run23.slurm                       # batch sweep, 16 configurations
├── collect.py                        # parses RESULT lines -> tables
├── results/
│   ├── matmul23_100418.out           # primary run, exclusive node
│   └── matmul23_100371.out           # independent replication
├── paper/
│   ├── data.py                       # measured values + derived quantities
│   ├── figures.py                    # the four figures
│   └── build_report.py               # assembles the PDF
└── AMS530_Project2_Problem2.3.pdf
```
 
---
 
## Build and run
 
On a cluster with OpenMPI and Slurm:
 
```bash
module load slurm
module load openmpi/gcc12.1/4.1.4
mpicc -O3 -funroll-loops -march=native -o matmul_mpi matmul_mpi.c -lm
```
 
A single configuration:
 
```bash
mpirun -np <P> ./matmul_mpi <N> [reps] [verify]
mpirun -np 4  ./matmul_mpi 256        # N=256, P=4, defaults
```
 
`N` must be divisible by `P`; the program validates this and aborts rather than
computing a wrong answer. Each run prints one machine-readable line:
 
```
RESULT N=1024 P=16 t_par=0.079955 t_dist=0.007456 t_comp=0.068115 \
       t_gath=0.004385 t_serlocal=0.332841 relerr=0.000e+00 verify=PASS
```
 
The full sweep, and the tables:
 
```bash
sbatch run23.slurm
python3 collect.py matmul23_<jobid>.out
```
 
The batch script rebuilds the binary inside the job so the binary always
matches the compute node's architecture. Exit status is non-zero if
verification fails, so a silent wrong answer cannot pass unnoticed.
 
---
 
## Regenerating the paper
 
```bash
cd paper
pip install reportlab matplotlib numpy pillow
python3 build_report.py "Your Name"
```
 
Every number in the PDF — tables, prose, figure axes — is computed from
`data.py` at build time rather than transcribed, so the document cannot
disagree with itself. To rebuild from a new sweep, replace the `RUN` dictionary
in `data.py` with the new `RESULT` values and re-run.
 
---
 
## Notes on methodology
 
Four decisions that affect whether the numbers mean anything:
 
**T₁ comes from a dedicated P = 1 run, not the in-job serial pass.** The
in-job serial multiply at N = 4096 measured 50.77–52.16 s against 50.83 s for a
dedicated run, roughly 3% slower, because the idle ranks busy-wait on cores
while rank 0 works. Using those would have inflated every speedup by that
margin.
 
**Wall time is the slowest rank's, found with `MPI_MAXLOC`.** Reducing each
phase independently with `MPI_MAX` draws three maxima from three different
ranks, and they do not sum to the measured total. An earlier version of this
harness had exactly that bug and reported breakdowns totalling 156% of wall
time.
 
**The local kernel is ordered i-k-j, not i-j-k.** Under `ijk` the inner loop
strides through B by N doubles and discards seven eighths of every cache line
fetched. Since the same kernel is both the serial baseline and the per-rank
work, a cache-hostile ordering would have inflated T₁ and T_P alike and left
the speedup ratios intact — while saturating the memory system everywhere and
concealing the cache effect that turned out to be the main finding.
 
**All sixteen ranks on one exclusively allocated node.** This removes the
interconnect and co-tenancy from consideration, so the shape of the curve is
set by the algorithm and the memory system alone.
 
The first hypothesis for the N = 1024 anomaly was contention from a co-resident
job. The replication run was executed specifically to test it, under exclusive
allocation; the effect reproduced, and the hypothesis was wrong. Both output
files are in `results/` so this is checkable.
 
---
 
## Environment
 
Intel Xeon E5-2683 v3 @ 2.00 GHz (Haswell-EP), 2 sockets × 14 cores, 35 MiB L3
per socket. SeaWulf, Stony Brook University, partition `short-28core`.
gcc 12.1, OpenMPI 4.1.4, IEEE-754 double precision throughout.
 
## References
 
1. Cannon, L. E. *A Cellular Computer to Implement the Kalman Filter Algorithm.* PhD thesis, Montana State University, 1969.
2. van de Geijn, R. A. and Watts, J. SUMMA: Scalable Universal Matrix Multiplication Algorithm. *Concurrency: Practice and Experience* 9(4), 1997.
3. Irony, D., Toledo, S. and Tiskin, A. Communication lower bounds for distributed-memory matrix multiplication. *JPDC* 64(9), 2004.
4. Grama, A., Gupta, A., Karypis, G. and Kumar, V. *Introduction to Parallel Computing*, 2nd ed. Addison-Wesley, 2003.
5. Karp, A. H. and Flatt, H. P. Measuring parallel processor performance. *CACM* 33(5), 1990.
6. Amdahl, G. M. Validity of the single processor approach. *AFIPS* 30, 1967.
7. Gustafson, J. L. Reevaluating Amdahl's law. *CACM* 31(5), 1988.
