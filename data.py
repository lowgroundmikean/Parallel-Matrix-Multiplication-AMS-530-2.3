"""
Measured data for AMS 530 Project 2, Problem 2.3.

Primary run  : Slurm job 100418, node sn149, exclusive allocation
Replication  : Slurm job 100371, shared allocation

Every number below is transcribed from the RESULT lines emitted by
matmul_mpi and collated by collect.py.  Derived quantities (speedup,
efficiency, Karp-Flatt, throughput, cache footprint) are COMPUTED here
rather than transcribed, so the paper cannot disagree with itself.
"""

SIZES = [64, 256, 1024, 4096]
PCOLS = [4, 8, 16]

# --- machine ---------------------------------------------------------
CPU         = "Intel Xeon E5-2683 v3 @ 2.00 GHz (Haswell-EP)"
CORES_SOCK  = 14
SOCKETS     = 2
CORES_NODE  = CORES_SOCK * SOCKETS           # 28
L3_SOCK_MiB = 35840 / 1024.0                 # 35.0 MiB, from lscpu
L3_NODE_MiB = L3_SOCK_MiB * SOCKETS          # 70.0 MiB

# --- primary run, job 100418 -----------------------------------------
# t_par is the slowest rank's total for the distribute/compute/gather
# phase; t_dist, t_comp, t_gath are that same rank's breakdown.
# key: (N, P) -> (t_par, t_dist, t_comp, t_gath)
RUN = {
    (64, 1):    (0.000097, 0.000004, 0.000091, 0.000003),
    (64, 4):    (0.000077, 0.000044, 0.000014, 0.000020),
    (64, 8):    (0.000100, 0.000063, 0.000008, 0.000029),
    (64, 16):   (0.000120, 0.000048, 0.000006, 0.000067),

    (256, 1):   (0.007554, 0.000073, 0.007410, 0.000071),
    (256, 4):   (0.002400, 0.000362, 0.001774, 0.000265),
    (256, 8):   (0.001606, 0.000497, 0.000897, 0.000211),
    (256, 16):  (0.001605, 0.000393, 0.000507, 0.000705),

    (1024, 1):  (0.323947, 0.001389, 0.321246, 0.001312),
    (1024, 4):  (0.115582, 0.004325, 0.084120, 0.027137),
    (1024, 8):  (0.072050, 0.014923, 0.054920, 0.002206),
    (1024, 16): (0.079955, 0.007456, 0.068115, 0.004385),

    (4096, 1):  (50.825712, 0.052571, 50.720469, 0.052671),
    (4096, 4):  (12.550124, 0.116729, 12.259691, 0.173705),
    (4096, 8):  (6.875919, 0.140316, 6.669177, 0.066426),
    (4096, 16): (4.976300, 0.156882, 4.703407, 0.116012),
}

# --- replication, job 100371 (t_par only) ----------------------------
REPL = {
    (64, 1): 0.000091,   (64, 4): 0.000080,
    (64, 8): 0.000096,   (64, 16): 0.000110,
    (256, 1): 0.007705,  (256, 4): 0.002421,
    (256, 8): 0.001715,  (256, 16): 0.001530,
    (1024, 1): 0.325084, (1024, 4): 0.115678,
    (1024, 8): 0.070021, (1024, 16): 0.079755,
    (4096, 1): 50.738504, (4096, 4): 12.514924,
    (4096, 8): 6.899651,  (4096, 16): 4.980042,
}

# t_comp at N=1024 in the replication, used to show the cliff repeated
REPL_COMP_1024 = {4: 0.082228, 8: 0.056185, 16: 0.063591}


# --- derived ---------------------------------------------------------

def t_par(n, p):   return RUN[(n, p)][0]
def t_dist(n, p):  return RUN[(n, p)][1]
def t_comp(n, p):  return RUN[(n, p)][2]
def t_gath(n, p):  return RUN[(n, p)][3]

def T1(n):         return RUN[(n, 1)][0]

def speedup(n, p):     return T1(n) / t_par(n, p)
def efficiency(n, p):  return speedup(n, p) / p

def karp_flatt(n, p):
    """Serial fraction implied by the measured speedup."""
    s = speedup(n, p)
    return (1.0 / s - 1.0 / p) / (1.0 - 1.0 / p)

def comm_frac(n, p):
    return (t_dist(n, p) + t_gath(n, p)) / t_par(n, p)

def gflops_rank(n, p):
    """Per-rank throughput during the compute phase, GFLOP/s.

    Work on one rank is 2*(N/P)*N*N floating-point operations.
    """
    flops = 2.0 * (n / p) * n * n
    return flops / t_comp(n, p) / 1.0e9

def gflops_agg(n, p):
    return gflops_rank(n, p) * p

def footprint_rank_MiB(n, p):
    """Private working set of one rank: all of B, plus its A and C blocks."""
    return (n * n + 2.0 * (n / p) * n) * 8.0 / 1048576.0

def footprint_socket_MiB(n, p):
    """L3 demanded per socket, ranks distributed evenly over sockets."""
    ranks_per_socket = max(p / SOCKETS, 1.0)
    return footprint_rank_MiB(n, p) * ranks_per_socket

def l3_occupancy(n, p):
    return footprint_socket_MiB(n, p) / L3_SOCK_MiB

def repl_delta(n, p):
    """Relative difference between the two independent runs."""
    a, b = t_par(n, p), REPL[(n, p)]
    return abs(a - b) / ((a + b) / 2.0)
