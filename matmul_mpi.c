/*
 * matmul_mpi.c  --  AMS 530 Project 2, Problem 2.3
 *
 * Parallel dense matrix multiplication  C = A * B  for square N x N matrices,
 * using a one-dimensional row-wise block decomposition over P MPI ranks.
 *
 * Data distribution
 * -----------------
 *   A : partitioned by rows.  Rank r owns rows [r*N/P, (r+1)*N/P).
 *   B : replicated.  Every rank holds the full N x N matrix.
 *   C : partitioned by rows, in the same layout as A, then gathered on rank 0.
 *
 * Rank 0 generates A and B, scatters the row blocks of A, broadcasts B,
 * every rank forms its own row block of C, rank 0 gathers the blocks and
 * checks the result against an independent serial multiplication of the
 * same A and B.
 *
 * Because each row of C is accumulated over k in exactly the same order in
 * the parallel and the serial code, the two results agree bit for bit; the
 * check below therefore uses a very tight tolerance.
 *
 * Usage:   mpirun -np P ./matmul_mpi N [reps] [verify]
 *            N       matrix dimension, must be divisible by P
 *            reps    timed repetitions, default 3 for N <= 1024 else 1
 *            verify  1 (default) runs the serial check, 0 skips it
 *
 * Build:   mpicc -O3 -funroll-loops -march=native -o matmul_mpi matmul_mpi.c -lm
 */

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */

static double *xalloc(size_t n)
{
    double *p = (double *) malloc(n * sizeof(double));
    if (p == NULL) {
        fprintf(stderr, "allocation of %zu doubles (%.1f MiB) failed\n",
                n, (double) n * sizeof(double) / 1048576.0);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    return p;
}

/*
 * C(rows x n) = A(rows x n) * B(n x n).
 *
 * The loops are ordered i, k, j rather than the textbook i, j, k.  With ikj
 * the innermost loop walks B and C with unit stride, so each cache line that
 * is fetched is fully consumed.  The textbook ordering strides through B by
 * n doubles and wastes most of every line.  This matters here: the same
 * kernel is used for the serial baseline and for the per-rank work, so a
 * cache-hostile kernel would inflate both T_1 and T_P and quietly distort
 * the speedup figures.
 */
static void matmul(const double *A, const double *B, double *C,
                   int rows, int n)
{
    memset(C, 0, (size_t) rows * n * sizeof(double));

    for (int i = 0; i < rows; i++) {
        const double *Ai = A + (size_t) i * n;
        double       *Ci = C + (size_t) i * n;

        for (int k = 0; k < n; k++) {
            const double  a  = Ai[k];
            const double *Bk = B + (size_t) k * n;

            for (int j = 0; j < n; j++)
                Ci[j] += a * Bk[j];
        }
    }
}

/* ------------------------------------------------------------------ */

int main(int argc, char **argv)
{
    int rank, P;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);

    const int N      = (argc > 1) ? atoi(argv[1]) : 1024;
    const int reps   = (argc > 2) ? atoi(argv[2]) : (N <= 1024 ? 3 : 1);
    const int verify = (argc > 3) ? atoi(argv[3]) : 1;

    if (N <= 0 || P <= 0 || N % P != 0) {
        if (rank == 0)
            fprintf(stderr,
                    "error: N (%d) must be positive and divisible by P (%d)\n",
                    N, P);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    const int    rows = N / P;                  /* rows of A and C per rank */
    const size_t nn   = (size_t) N * N;         /* elements in a full matrix */
    const size_t blk  = (size_t) rows * N;      /* elements in one row block */

    /* MPI collective counts are int; confirm nothing overflows. */
    if (nn > (size_t) 2147483647) {
        if (rank == 0)
            fprintf(stderr, "error: N=%d gives N*N > INT_MAX\n", N);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    double *A = NULL, *C = NULL, *Cser = NULL;  /* full matrices, rank 0 only */
    double *B    = xalloc(nn);                  /* replicated on every rank  */
    double *locA = xalloc(blk);
    double *locC = xalloc(blk);

    if (rank == 0) {
        A    = xalloc(nn);
        C    = xalloc(nn);
        Cser = verify ? xalloc(nn) : NULL;

        srand48(20261018L);                     /* fixed seed, reproducible */
        for (size_t t = 0; t < nn; t++) A[t] = drand48() - 0.5;
        for (size_t t = 0; t < nn; t++) B[t] = drand48() - 0.5;
    }

    /* ---------------- timed parallel phase ---------------- */
    /*
     * One untimed warm-up pass for the smaller cases, so that first-touch
     * page faults and the first-call cost of the collectives do not land in
     * the measurement.  Skipped above N = 1024, where a warm-up pass would
     * cost more wall time than it saves in noise.
     */
    const int warmup = (N <= 1024) ? 1 : 0;

    double best = 1.0e30, b_dist = 0.0, b_comp = 0.0, b_gath = 0.0;

    for (int r = 0; r < reps + warmup; r++) {

        MPI_Barrier(MPI_COMM_WORLD);
        const double t0 = MPI_Wtime();

        /* distribute: row blocks of A out, all of B to everyone */
        MPI_Scatter(A,    (int) blk, MPI_DOUBLE,
                    locA, (int) blk, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        MPI_Bcast(B, (int) nn, MPI_DOUBLE, 0, MPI_COMM_WORLD);

        const double t1 = MPI_Wtime();

        /* local work: this rank's rows of C */
        matmul(locA, B, locC, rows, N);

        const double t2 = MPI_Wtime();

        /* collect */
        MPI_Gather(locC, (int) blk, MPI_DOUBLE,
                   C,    (int) blk, MPI_DOUBLE, 0, MPI_COMM_WORLD);

        const double t3 = MPI_Wtime();

        /*
         * The cost of a parallel step is set by the slowest rank.  Taking an
         * independent MPI_MAX of each phase would be wrong: the rank that
         * waited longest in the scatter is generally not the rank that spent
         * longest computing, so the three maxima would come from three
         * different ranks and would not sum to the measured total.  Instead
         * find the slowest rank by total time with MPI_MAXLOC, then take that
         * one rank's internal breakdown, which does sum exactly.
         */
        struct { double val; int rank; } in, out;
        in.val  = t3 - t0;
        in.rank = rank;
        MPI_Allreduce(&in, &out, 1, MPI_DOUBLE_INT, MPI_MAXLOC,
                      MPI_COMM_WORLD);

        double slow[4] = { t3 - t0, t1 - t0, t2 - t1, t3 - t2 };
        MPI_Bcast(slow, 4, MPI_DOUBLE, out.rank, MPI_COMM_WORLD);

        if (r >= warmup && rank == 0 && slow[0] < best) {
            best   = slow[0];
            b_dist = slow[1];
            b_comp = slow[2];
            b_gath = slow[3];
        }
    }

    /* ---------------- serial baseline and verification ---------------- */
    /*
     * This serial pass is the correctness check required by the assignment.
     * Its timing is reported but is NOT the T_1 used for speedup: while rank
     * 0 runs it the other P-1 ranks are idle inside MPI and, with the default
     * busy-wait progress engine, they still occupy cores and memory
     * bandwidth.  T_1 for the speedup table is taken from a dedicated P = 1
     * run of this same binary, where no such contention exists.
     */
    double t_ser = 0.0, relerr = 0.0;
    int    ok    = 1;

    if (rank == 0 && verify) {
        const double s0 = MPI_Wtime();
        matmul(A, B, Cser, N, N);
        t_ser = MPI_Wtime() - s0;

        double maxerr = 0.0, maxabs = 0.0;
        for (size_t t = 0; t < nn; t++) {
            const double e = fabs(C[t] - Cser[t]);
            const double m = fabs(Cser[t]);
            if (e > maxerr) maxerr = e;
            if (m > maxabs) maxabs = m;
        }
        relerr = (maxabs > 0.0) ? maxerr / maxabs : maxerr;
        ok     = (relerr <= 1.0e-12);
    }

    /* ---------------- one machine-readable line per run ---------------- */

    if (rank == 0) {
        printf("RESULT N=%d P=%d t_par=%.6f t_dist=%.6f t_comp=%.6f "
               "t_gath=%.6f t_serlocal=%.6f relerr=%.3e verify=%s\n",
               N, P, best, b_dist, b_comp, b_gath, t_ser, relerr,
               verify ? (ok ? "PASS" : "FAIL") : "SKIP");
        fflush(stdout);
    }

    free(B); free(locA); free(locC);
    if (rank == 0) { free(A); free(C); free(Cser); }

    MPI_Finalize();
    return (rank == 0 && verify && !ok) ? 2 : 0;
}
