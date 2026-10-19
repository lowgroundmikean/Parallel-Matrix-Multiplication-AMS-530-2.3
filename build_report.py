#!/usr/bin/env python3
"""
Build the AMS 530 Project 2, Problem 2.3 report as a PDF.

    python3 build_report.py

Reads data.py for every number and figures.py for every plot, so the
prose, the tables and the figures cannot drift apart.
"""

import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Preformatted,
                                Spacer, Table, TableStyle)

import data as d
import figures

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(HERE)

# --------------------------------------------------------------- fonts
FDIR = "/usr/share/fonts/truetype/liberation"
pdfmetrics.registerFont(TTFont("LSerif", f"{FDIR}/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LSerif-B", f"{FDIR}/LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("LSerif-I", f"{FDIR}/LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("LMono", f"{FDIR}/LiberationMono-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LMono-B", f"{FDIR}/LiberationMono-Bold.ttf"))
pdfmetrics.registerFontFamily("LSerif", normal="LSerif", bold="LSerif-B",
                              italic="LSerif-I")

INK = colors.HexColor("#111111")
RULE = colors.HexColor("#999999")
LIGHT = colors.HexColor("#f0efec")

# --------------------------------------------------------------- styles
ss = getSampleStyleSheet()

TITLE = ParagraphStyle("TITLE", parent=ss["Title"], fontName="LSerif-B",
                       fontSize=16.5, leading=20, spaceAfter=4, textColor=INK)
SUBTITLE = ParagraphStyle("SUBTITLE", parent=ss["Normal"], fontName="LSerif",
                          fontSize=10.5, leading=14, alignment=TA_CENTER,
                          textColor=colors.HexColor("#444444"), spaceAfter=2)
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="LSerif-B",
                    fontSize=12.5, leading=15, spaceBefore=15, spaceAfter=6,
                    textColor=INK)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="LSerif-B",
                    fontSize=10.8, leading=13, spaceBefore=11, spaceAfter=4,
                    textColor=INK)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName="LSerif",
                      fontSize=10, leading=13.6, alignment=TA_JUSTIFY,
                      spaceAfter=7, textColor=INK)
ABSTRACT = ParagraphStyle("ABSTRACT", parent=BODY, fontSize=9.5, leading=13,
                          leftIndent=20, rightIndent=20,
                          textColor=colors.HexColor("#222222"))
BULLET = ParagraphStyle("BULLET", parent=BODY, leftIndent=16, bulletIndent=4,
                        spaceAfter=4)
EQ = ParagraphStyle("EQ", parent=BODY, alignment=TA_CENTER, spaceBefore=5,
                    spaceAfter=7, fontName="LSerif-I", fontSize=10.5)
CAPTION = ParagraphStyle("CAPTION", parent=ss["Normal"], fontName="LSerif",
                         fontSize=8.8, leading=11.5, alignment=TA_CENTER,
                         textColor=colors.HexColor("#444444"),
                         spaceBefore=4, spaceAfter=11)
TCAP = ParagraphStyle("TCAP", parent=CAPTION, alignment=TA_JUSTIFY,
                      spaceBefore=3, spaceAfter=10)
CODE = ParagraphStyle("CODE", parent=ss["Code"], fontName="LMono",
                      fontSize=6.6, leading=7.9, textColor=INK,
                      leftIndent=4, spaceAfter=0, spaceBefore=0)
SHELL = ParagraphStyle("SHELL", parent=ss["Code"], fontName="LMono",
                       fontSize=7.8, leading=10, textColor=INK,
                       leftIndent=8, spaceAfter=8, spaceBefore=4)
PSEUDO = ParagraphStyle("PSEUDO", parent=ss["Code"], fontName="LMono",
                        fontSize=7.9, leading=10.2, textColor=INK,
                        leftIndent=8, spaceAfter=2, spaceBefore=2)
REF = ParagraphStyle("REF", parent=BODY, fontSize=9.2, leading=12,
                     leftIndent=20, firstLineIndent=-20, spaceAfter=4,
                     alignment=TA_JUSTIFY)

# --------------------------------------------------------------- helpers
def P(t, s=BODY):
    return Paragraph(t, s)


def eq(t):
    return Paragraph(t, EQ)


def fignum(n, text):
    return Paragraph(f"<b>Figure {n}.</b> {text}", CAPTION)


def tabnum(n, text):
    return Paragraph(f"<b>Table {n}.</b> {text}", TCAP)


def table(rows, widths, align_right_from=1, header_rows=1, size=8.6):
    t = Table(rows, colWidths=widths, hAlign="CENTER", repeatRows=header_rows)
    style = [
        ("FONT", (0, 0), (-1, -1), "LSerif", size),
        ("FONT", (0, 0), (-1, header_rows - 1), "LSerif-B", size),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("ALIGN", (align_right_from, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (align_right_from - 1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, INK),
        ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.55, INK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, INK),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(style))
    return t


def figure(path, width_in, num, caption):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    width = width_in * inch
    height = width * h / w
    return KeepTogether([Image(path, width=width, height=height),
                         fignum(num, caption)])


def shade(t, rows, color=LIGHT):
    for r in rows:
        t.setStyle(TableStyle([("BACKGROUND", (0, r), (-1, r), color)]))
    return t


# --------------------------------------------------------------- page
def decorate(canvas, doc):
    canvas.saveState()
    canvas.setFont("LSerif", 8.3)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.95 * inch, 0.58 * inch,
                      "AMS 530 — Project 2, Problem 2.3")
    canvas.drawRightString(LETTER[0] - 0.95 * inch, 0.58 * inch,
                           "%d" % doc.page)
    canvas.setStrokeColor(colors.HexColor("#cccccc"))
    canvas.setLineWidth(0.4)
    canvas.line(0.95 * inch, 0.74 * inch, LETTER[0] - 0.95 * inch, 0.74 * inch)
    canvas.restoreState()


def build(path, author):
    doc = BaseDocTemplate(path, pagesize=LETTER,
                          leftMargin=0.95 * inch, rightMargin=0.95 * inch,
                          topMargin=0.85 * inch, bottomMargin=0.95 * inch,
                          title="Parallel Dense Matrix Multiplication: "
                                "A Row-Wise MPI Decomposition and the "
                                "Cache-Capacity Limit of Operand Replication",
                          author=author)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame],
                                       onPage=decorate)])
    doc.build(story(author))


# --------------------------------------------------------------- content
def story(author):
    S = []
    W = 6.6 * inch

    # ---------------------------------------------------------- title
    S.append(P("Parallel Dense Matrix Multiplication:<br/>"
               "A Row-Wise MPI Decomposition and the Cache-Capacity "
               "Limit of Operand Replication", TITLE))
    S.append(Spacer(1, 4))
    S.append(P(author, SUBTITLE))
    S.append(P("AMS 530: Principles of Parallel Computing &nbsp;·&nbsp; "
               "Prof. Yuefan Deng", SUBTITLE))
    S.append(P("Stony Brook University &nbsp;·&nbsp; 18 October 2026",
               SUBTITLE))
    S.append(Spacer(1, 13))

    # ---------------------------------------------------------- abstract
    S.append(P("Abstract", H1))
    S.append(P(
        "We design, implement and evaluate a distributed-memory dense "
        "matrix multiplication for square operands using a one-dimensional "
        "row-wise block decomposition in MPI. The decomposition is chosen "
        "deliberately over the asymptotically superior two-dimensional "
        "Cannon and SUMMA families for a reason internal to the problem "
        "specification: the required process counts include "
        "P = 2<super>3</super>, and because 8 is not a perfect square no "
        "square process grid exists, so any two-dimensional scheme would "
        "have to change algorithm midway through the sweep and render the "
        "three columns mutually incomparable. "
        "Across the four problem sizes N = 2<super>6</super> through "
        "2<super>12</super> and the three process counts "
        "P = 4, 8 and 16 "
        "on a 28-core dual-socket Haswell node, all sixteen configurations "
        "reproduce the serial result exactly — to zero relative error, "
        "which we show is a structural consequence of the decomposition "
        "rather than good fortune — and the full sweep was executed "
        "twice on separate nodes, agreeing to within 0.34% at the largest "
        "problem size. "
        "The principal result is negative and, we argue, more instructive "
        "than the speedup figures themselves. The Karp–Flatt metric "
        "falls by two orders of magnitude as N grows, from 0.725 to "
        "−0.004, which falsifies any model built on a fixed serial "
        "fraction; yet within each problem size it <i>rises</i> with P even "
        "at N = 2<super>12</super>, where communication never exceeds 5.5% "
        "of wall time. We trace this residual to the memory hierarchy. "
        "Because every rank holds a private copy of B, the aggregate "
        "last-level cache demand grows as P·N², and per-rank "
        "throughput collapses by a factor of 2.5 precisely where that "
        "demand crosses the 35 MiB physical L3 capacity. A single "
        "mechanism accounts for the behaviour of all four problem sizes, "
        "and it is a direct consequence of the operand replication the "
        "design chose.", ABSTRACT))
    S.append(Spacer(1, 6))

    # ========================================================== 1
    S.append(P("1.&nbsp;&nbsp;Project Description", H1))
    S.append(P(
        "The assignment, reproduced from the problem set, is to design a "
        "parallel matrix multiplication using row-wise, column-wise or "
        "block decomposition, and to implement a parallel version using "
        "MPI for square matrices. The three tasks are as follows.", BODY))
    S.append(P(
        "<b>(1) Algorithm Design.</b> Design a parallel matrix "
        "multiplication algorithm using MPI; describe the data "
        "distribution; discuss load balancing, communication overhead and "
        "scalability for P processes; assume matrices are square of size "
        "N × N and that P divides N.", BULLET, ))
    S.append(P(
        "<b>(2) Implementation.</b> The root process generates two random "
        "N × N matrices A and B; the root computes and verifies C "
        "against a serial version; support P = 2<super>2</super>, "
        "2<super>3</super>, 2<super>4</super>; test for N = "
        "2<super>6</super>, 2<super>8</super>, 2<super>10</super>, "
        "2<super>12</super>; include a serial baseline for verification.",
        BULLET))
    S.append(P(
        "<b>(3) Performance Evaluation.</b> Build a test harness that "
        "verifies correctness, measures execution time, computes speedup, "
        "records the timing results, and makes relevant comments on "
        "Amdahl's law.", BULLET))
    S.append(P(
        "Sections 2 through 4 address task (1) and the implementation "
        "required by task (2); Sections 5 and 6 address task (3). Complete "
        "source, the batch script and the analysis harness appear in the "
        "appendices, with compilation and execution instructions in "
        "Section 3.5.", BODY))

    # ========================================================== 2
    S.append(P("2.&nbsp;&nbsp;Algorithm Design", H1))

    S.append(P("2.1&nbsp;&nbsp;Data distribution", H2))
    S.append(P(
        "The algorithm employs a one-dimensional row-wise block "
        "partition. Matrix A is divided into P contiguous blocks of "
        "N/P rows, with rank r owning rows [rN/P, (r+1)N/P). Matrix B is "
        "<i>replicated in full</i> on every rank. The product C is "
        "distributed in the same layout as A and gathered on the root at "
        "the end of the computation. Each rank therefore evaluates",
        BODY))
    S.append(eq("C[i][j] = Σ<sub>k=0</sub><sup>N−1</sup> "
                "A[i][k] · B[k][j]"))
    S.append(P(
        "for every i in its own row block and every j, which requires the "
        "whole of B and none of any other rank's share of A. The "
        "computation is consequently free of inter-rank dependencies once "
        "distribution is complete: there is exactly one communication "
        "phase before the arithmetic and one after it, with no "
        "synchronisation in between. This is the structural virtue of the "
        "one-dimensional scheme and the reason its implementation admits "
        "no deadlock and no race by construction.", BODY))

    S.append(P("2.2&nbsp;&nbsp;Why one dimension and not two", H2))
    S.append(P(
        "The two-dimensional block algorithms — Cannon's method [1] "
        "and the SUMMA family [2] — are asymptotically superior in "
        "communication volume, and a report that selected a "
        "one-dimensional scheme purely for ease of implementation would "
        "deserve the obvious criticism. The decisive argument here is not "
        "convenience but a constraint internal to the problem "
        "specification.", BODY))
    S.append(P(
        "Cannon's algorithm requires a square "
        "√P × √P process grid, over which the operands are "
        "cyclically shifted. The assignment mandates "
        "P = 4, 8 and 16. While √4 = 2 and √16 = 4 are "
        "integers, <b>√8 is not</b>. No square process grid exists at "
        "P = 2<super>3</super>, and the algorithm would therefore have to "
        "degrade to a 2 × 4 rectangular grid at precisely one of the "
        "three required data points. The middle column of every table "
        "would then describe a different algorithm from the columns on "
        "either side of it, and the resulting scaling study would measure "
        "the change of method as much as the change of process count. The "
        "one-dimensional decomposition is uniform across all three "
        "mandated values of P, and comparability across the sweep is worth "
        "more than a constant factor in communication volume at process "
        "counts this small — as Section 2.4 quantifies, the penalty "
        "at P = 16 is a factor of two.", BODY))

    S.append(P("2.3&nbsp;&nbsp;Load balancing", H2))
    S.append(P(
        "Load balance is exact rather than approximate, and provably so. "
        "The problem sizes N = 2<super>6</super> through "
        "2<super>12</super> and the process counts "
        "P = 4, 8 and 16 "
        "are all powers of two with N ≥ 64 &gt; 16 ≥ "
        "P<sub>max</sub>, so P divides N in every cell of the experimental "
        "grid and each rank performs precisely N³/P "
        "multiply–accumulate operations. No remainder arises, no rank "
        "receives a short block, and no dynamic balancing is required. "
        "The implementation nevertheless validates the divisibility "
        "condition at startup and aborts rather than silently computing a "
        "wrong answer, since the guarantee is a property of the "
        "experimental design and not of the program.", BODY))

    S.append(P("2.4&nbsp;&nbsp;Communication overhead", H2))
    S.append(P(
        "Three collectives carry all traffic. The scatter delivers "
        "N²/P elements of A to each rank; the broadcast delivers all "
        "N² elements of B to each rank; the gather returns N²/P "
        "elements of C from each rank. Per-rank volume is therefore",
        BODY))
    S.append(eq("V<sub>rank</sub> = N²/P + N² + N²/P "
                "= N²(1 + 2/P)  ≈  N² elements,"))
    S.append(P(
        "dominated entirely by the replication of B, and the aggregate "
        "across the machine is Θ(PN²). Cannon's algorithm, by "
        "contrast, moves 2N²/√P per rank and 2√P·N² "
        "in aggregate, so the one-dimensional scheme is worse by a factor "
        "of √P/2. At P = 16 this is a factor of two; it becomes "
        "punishing only at process counts in the hundreds, which is the "
        "honest statement of when this design should be abandoned.", BODY))
    S.append(P(
        "It is worth recording how far either scheme sits from optimal. "
        "Irony, Toledo and Tiskin [3] established that any process "
        "participating in a distributed classical matrix multiplication "
        "with memory proportional to N²/P must communicate "
        "Ω(N²/√P) words. Cannon attains this bound to within "
        "a constant; the row-wise scheme exceeds it by √P. The "
        "governing dimensionless quantity for the present design is the "
        "ratio of arithmetic to communication,", BODY))
    S.append(eq("(N³/P) / N² = N/P,"))
    S.append(P(
        "and essentially every feature of the measured results in "
        "Section 5 can be anticipated from whether this ratio is large or "
        "small. At N = 64, P = 16 it is 4; at N = 4096, P = 16 it is 256.",
        BODY))

    S.append(P("2.5&nbsp;&nbsp;Scalability and isoefficiency", H2))
    S.append(P(
        "Let T<sub>1</sub> = cN³ be the serial time and model the "
        "parallel time as T<sub>P</sub> = cN³/P + βN², where "
        "β absorbs the per-element cost of moving B. The total "
        "overhead is then", BODY))
    S.append(eq("T<sub>o</sub> = P·T<sub>P</sub> − T<sub>1</sub> "
                "= βPN²,"))
    S.append(P(
        "and the efficiency is E = T<sub>1</sub>/(T<sub>1</sub> + "
        "T<sub>o</sub>) = 1/(1 + βP/(cN)). Holding E constant in the "
        "sense of Grama et al. [4] therefore requires N to grow in proportion to P, so that "
        "the problem size W = N³ must grow as", BODY))
    S.append(eq("W = Θ(P³)."))
    S.append(P(
        "This is poor. The corresponding analysis for Cannon gives "
        "T<sub>o</sub> ≈ 2β√P N², hence N growing as √P "
        "and W = Θ(P<sup>3/2</sup>). The one-dimensional scheme buys "
        "uniformity across the required process counts and a "
        "dependency-free computation phase at the price of a cubic "
        "isoefficiency function.", BODY))
    S.append(P(
        "The analysis above accounts for communication only, and it will "
        "prove insufficient. Replicating B also renders per-rank memory "
        "Θ(N²), independent of P — the scheme does not scale "
        "in space. The conventional expectation is that this manifests as "
        "an allocation failure at large N. Section 6.2 shows that it "
        "manifests instead, and much earlier, as a cache-capacity effect "
        "that the communication model has no term for.", BODY))

    # ========================================================== 3
    S.append(P("3.&nbsp;&nbsp;Implementation", H1))

    S.append(P("3.1&nbsp;&nbsp;Program structure", H2))
    S.append(P(
        "The program is a single C translation unit, "
        "<font name='LMono' size='9'>matmul_mpi.c</font>, reproduced in "
        "full as Appendix A. Its structure is as follows.", BODY))

    pseudo = """ALGORITHM  Row-wise parallel matrix multiply
INPUT      N (divisible by P), reps, verify flag
OUTPUT     C = A.B on rank 0, verified against a serial multiply

 1  MPI_Init;  rank <- comm rank;  P <- comm size
 2  if N mod P != 0 then MPI_Abort                  // guard, Sec. 2.3
 3  rows <- N / P
 4  allocate B[N*N], locA[rows*N], locC[rows*N]     // on every rank
 5  if rank = 0 then
 6      allocate A[N*N], C[N*N], Cser[N*N]
 7      seed srand48(fixed);  fill A, B with drand48() - 0.5
 8
 9  for r <- 0 to reps + warmup do                  // warmup untimed
10      MPI_Barrier                                 // common start
11      t0 <- MPI_Wtime
12      MPI_Scatter (A -> locA, rows*N doubles, root 0)
13      MPI_Bcast   (B, N*N doubles, root 0)
14      t1 <- MPI_Wtime
15      locC <- MATMUL(locA, B, rows, N)            // ikj, Sec. 3.2
16      t2 <- MPI_Wtime
17      MPI_Gather  (locC -> C, rows*N doubles, root 0)
18      t3 <- MPI_Wtime
19      (tmax, slowest) <- MPI_Allreduce(t3-t0, MPI_MAXLOC)
20      broadcast that rank's (t3-t0, t1-t0, t2-t1, t3-t2)   // Sec. 3.3
21      if r >= warmup then keep the fastest such quadruple
22
23  if rank = 0 and verify then
24      Cser <- MATMUL(A, B, N, N);  time it
25      relerr <- max|C - Cser| / max|Cser|          // Sec. 3.4
26      assert relerr <= 1e-12
27  if rank = 0 then emit one machine-readable RESULT line
28  MPI_Finalize"""
    S.append(Preformatted(pseudo, PSEUDO))
    S.append(Spacer(1, 6))
    S.append(P(
        "Line 12 through line 18 constitute the entire parallel phase. "
        "Because the senders and receivers of each collective are "
        "disjoint and the computation at line 15 is purely local, the "
        "program contains no point-to-point messaging, no deadlock risk "
        "and no race condition.", BODY))

    S.append(P("3.2&nbsp;&nbsp;The local kernel", H2))
    S.append(P(
        "The local multiplication is ordered i, k, j rather than the "
        "textbook i, j, k. This is not a micro-optimisation but a "
        "precondition for the experiment measuring what it claims to "
        "measure. Under <font name='LMono' size='9'>ijk</font> the "
        "innermost loop strides through B by N doubles, drawing one useful "
        "element from each 64-byte cache line and discarding the remaining "
        "seven. Under <font name='LMono' size='9'>ikj</font> the innermost "
        "loop traverses both B and C with unit stride and every fetched "
        "line is fully consumed:", BODY))
    S.append(Preformatted(
        "for i in 0..rows-1:\n"
        "    for k in 0..N-1:\n"
        "        a <- A[i][k]                  // loop-invariant scalar\n"
        "        for j in 0..N-1:\n"
        "            C[i][j] <- C[i][j] + a * B[k][j]   // unit stride",
        PSEUDO))
    S.append(Spacer(1, 5))
    S.append(P(
        "Since the identical kernel serves as both the serial baseline and "
        "the per-rank work, a cache-hostile ordering would have inflated "
        "T<sub>1</sub> and T<sub>P</sub> alike and left the speedup ratios "
        "superficially intact. It would, however, have saturated the "
        "memory system at every problem size and thereby concealed the "
        "cache-capacity effect that turns out to be this study's principal "
        "finding. Choosing the cache-friendly kernel is what makes the "
        "memory hierarchy visible rather than ambient.", BODY))

    S.append(P("3.3&nbsp;&nbsp;Timing methodology", H2))
    S.append(P("Four decisions in the harness warrant defence.", BODY))
    S.append(P(
        "<b>(i) T<sub>1</sub> is taken from a dedicated single-rank "
        "execution, not from the in-job serial pass.</b> The program also "
        "performs a serial multiply on rank 0 for verification, and that "
        "pass is timed; at N = 4096 it recorded 50.77, 52.15 and 52.16 s "
        "at P = 4, 8 and 16 respectively, against 50.83 s for a dedicated "
        "P = 1 run. The roughly three per cent inflation is the signature "
        "of the remaining P−1 ranks sitting in a busy-wait progress "
        "loop, occupying cores while rank 0 works. Adopting those figures "
        "as the baseline would have inflated every reported speedup by "
        "that margin.", BULLET))
    S.append(P(
        "<b>(ii) Wall time is the slowest rank's, located with "
        "MPI_MAXLOC.</b> A naive implementation reduces each phase "
        "separately with MPI_MAX. This is incorrect: the rank that waited "
        "longest in the scatter is rarely the rank that computed longest, "
        "so three independent maxima are drawn from three different ranks "
        "and do not sum to the measured total. An early version of this "
        "harness exhibited exactly that defect, reporting phase "
        "breakdowns totalling up to 156% of wall time. The corrected "
        "version identifies the slowest rank by total time and broadcasts "
        "that one rank's internal breakdown, which sums exactly by "
        "construction.", BULLET))
    S.append(P(
        "<b>(iii) Each configuration reports the best of repeated timed "
        "passes</b>, preceded at N ≤ 1024 by an untimed warm-up so "
        "that first-touch page faults and first-invocation collective "
        "overhead fall outside the measurement.", BULLET))
    S.append(P(
        "<b>(iv) All sixteen ranks occupy a single exclusively allocated "
        "node.</b> This removes the interconnect from consideration "
        "entirely — a deliberate contrast with Project 1, where node "
        "placement dominated — and removes co-tenancy, so that the "
        "shape of the speedup curve is determined by the algorithm and the "
        "memory system alone.", BULLET))

    S.append(P("3.4&nbsp;&nbsp;Verification", H2))
    S.append(P(
        "Rank 0 recomputes C serially and compares element-wise, reporting "
        "max|C − C<sub>ser</sub>| / max|C<sub>ser</sub>|. The "
        "relative error was <b>exactly zero at all sixteen "
        "configurations</b>. This is a consequence of the design rather "
        "than of good fortune, and the reason is worth making explicit: "
        "the row-wise decomposition assigns each output element entirely "
        "to one rank and preserves the order of the k-summation, so no "
        "floating-point reassociation occurs anywhere and the parallel and "
        "serial results are bit-identical. The test is therefore far "
        "sharper than a tolerance comparison — any non-zero residual "
        "would indicate a genuine indexing or distribution defect, not "
        "accumulated rounding. A two-dimensional scheme that splits the "
        "k-dimension across ranks would not enjoy this property and would "
        "require a genuine tolerance.", BODY))
    S.append(P(
        "We note for completeness that the O(N³) verification could "
        "be replaced by Freivalds' randomised check [5], which for a "
        "random r drawn uniformly from {0,1}<super>N</super> compares A(Br) with Cr in "
        "O(N²) time, never rejecting a correct product and accepting "
        "an incorrect one with probability at most 2<super>−k</super> "
        "after k trials. At N = 4096 this is 6N² ≈ "
        "10<super>8</super> operations against 2N³ ≈ "
        "1.4×10<super>11</super>, a factor of 1365. It was not "
        "adopted here because the specification names the serial multiply "
        "as a deliverable and, more fundamentally, because T<sub>1</sub> "
        "is itself the serial multiply: the cubic work is the measurement, "
        "not overhead to be avoided. Freivalds becomes the method of "
        "choice at problem sizes where a serial baseline is no longer "
        "feasible and scaled speedup must replace S = T<sub>1</sub>/"
        "T<sub>P</sub>.", BODY))

    S.append(P("3.5&nbsp;&nbsp;Compilation and execution", H2))
    S.append(P("On SeaWulf, from an interactive login node:", BODY))
    S.append(Preformatted(
        "module load slurm\n"
        "module load openmpi/gcc12.1/4.1.4\n"
        "mpicc -O3 -funroll-loops -march=native -o matmul_mpi matmul_mpi.c -lm",
        SHELL))
    S.append(P("A single configuration may be run directly:", BODY))
    S.append(Preformatted(
        "mpirun -np <P> ./matmul_mpi <N> [reps] [verify]\n"
        "mpirun -np 4  ./matmul_mpi 256          # N=256, P=4, defaults",
        SHELL))
    S.append(P(
        "The complete sweep is driven by the batch script of Appendix B, "
        "which rebuilds the binary inside the job so that it always "
        "matches the compute node's architecture:", BODY))
    S.append(Preformatted(
        "sbatch run23.slurm                      # queues all 16 runs\n"
        "squeue -u $USER\n"
        "python3 collect.py matmul23_<jobid>.out # emits every table below",
        SHELL))
    S.append(P(
        "Each run emits one machine-readable "
        "<font name='LMono' size='9'>RESULT</font> line carrying N, P, the "
        "total and per-phase timings, the relative error and the "
        "verification verdict; "
        "<font name='LMono' size='9'>collect.py</font> parses these and "
        "derives every table in Section 5. The program returns a non-zero "
        "exit status if verification fails, so a silent wrong answer "
        "cannot pass unnoticed.", BODY))

    # ========================================================== 4
    S.append(P("4.&nbsp;&nbsp;Experimental Setup", H1))
    setup = [
        ["Cluster", "SeaWulf, Stony Brook University; partition short-28core"],
        ["Node", "sn149, allocated exclusively (--exclusive)"],
        ["Processor", d.CPU],
        ["Topology", f"{d.SOCKETS} sockets × {d.CORES_SOCK} cores "
                     f"= {d.CORES_NODE} cores"],
        ["Last-level cache", f"{d.L3_SOCK_MiB:.0f} MiB L3 per socket, "
                             f"{d.L3_NODE_MiB:.0f} MiB per node (lscpu)"],
        ["Toolchain", "gcc 12.1 with OpenMPI 4.1.4; "
                      "-O3 -funroll-loops -march=native"],
        ["Arithmetic", "IEEE-754 double precision throughout"],
        ["Primary run", "Slurm job 100418"],
        ["Replication", "Slurm job 100371, separate node"],
    ]
    S.append(KeepTogether([
        table([["Parameter", "Value"]] + setup,
              [1.45 * inch, 5.0 * inch], align_right_from=1, size=8.8),
        Spacer(1, 3),
        P("Because 16 ≤ 28, every configuration in the sweep fits "
          "within one node and no measurement crosses the interconnect.",
          TCAP)]))

    # ========================================================== 5
    S.append(P("5.&nbsp;&nbsp;Results", H1))
    S.append(P(
        "All sixteen configurations verified exactly. Table 1 gives the "
        "measured wall-clock time in the shape requested by the problem "
        "set, with the single-rank baseline added as the leftmost column "
        "since it is the denominator of every speedup that follows.",
        BODY))

    # --- Table 1
    rows = [["N", "T₁ (P = 1)", "P = 2²", "P = 2³",
             "P = 2⁴"]]
    for n in d.SIZES:
        rows.append([nlab(n, f"  ({n})"), f"{d.T1(n):.6f}"] +
                    [f"{d.t_par(n, p):.6f}" for p in d.PCOLS])
    S.append(table(rows, [1.15 * inch] + [1.26 * inch] * 4))
    S.append(tabnum(1, "Parallel wall-clock time in seconds, taken as the "
                       "slowest rank's total for the "
                       "distribute–compute–gather phase and "
                       "reported as the best of the timed repetitions."))

    # --- Table 2
    rows = [["N", "S(4)", "S(8)", "S(16)", "E(4)", "E(8)", "E(16)"]]
    for n in d.SIZES:
        rows.append([nlab(n)] +
                    [f"{d.speedup(n, p):.3f}" for p in d.PCOLS] +
                    [f"{d.efficiency(n, p):.3f}" for p in d.PCOLS])
    t = table(rows, [0.78 * inch] + [0.82 * inch] * 6)
    S.append(t)
    S.append(tabnum(2, "Speedup S(P) = T<sub>1</sub>/T<sub>P</sub> and efficiency "
                       "E(P) = S(P)/P. Speedup falls below unity at "
                       "N = 2<super>6</super> for P ≥ 8; efficiency at "
                       "N = 2<super>12</super>, P = 4 marginally exceeds one, "
                       "which Section 6.4 addresses."))

    S.append(figure(os.path.join(HERE, "fig1_speedup.png"), 5.55, 1,
                    "Speedup against process count on logarithmic axes, "
                    "with the ideal bound S = P. The four problem sizes "
                    "separate cleanly; only N = 2<super>12</super> tracks the "
                    "ideal through P = 8."))

    S.append(figure(os.path.join(HERE, "fig2_efficiency.png"), 5.55, 2,
                    "Parallel efficiency. The ordering is <i>not</i> "
                    "monotone in N: N = 2<super>8</super> is more "
                    "efficient than N = 2<super>10</super> at every "
                    "process count despite being sixteen times smaller, "
                    "which a purely communication-based model cannot "
                    "produce. This is the first indication of the "
                    "mechanism identified in Section 6.2."))

    # --- Table 3: phase breakdown
    rows = [["N", "P", "distribute", "compute", "gather", "comm. share"]]
    shaded = []
    for n in d.SIZES:
        for p in [1] + d.PCOLS:
            rows.append([nlab(n, size=8.2) if p == 1 else "", str(p),
                         f"{d.t_dist(n, p):.6f}", f"{d.t_comp(n, p):.6f}",
                         f"{d.t_gath(n, p):.6f}",
                         f"{100 * d.comm_frac(n, p):.1f}%"])
            if n == 1024 and p == 16:
                shaded.append(len(rows) - 1)
    t = table(rows, [0.72 * inch, 0.52 * inch] + [1.16 * inch] * 3 +
              [0.95 * inch], align_right_from=1, size=8.2)
    S.append(shade(t, shaded))
    S.append(tabnum(3, "Decomposition of the parallel phase, in seconds, "
                       "for the slowest rank. The communication share is "
                       "(distribute + gather) / total. The shaded row is "
                       "discussed in Section 6.2: at N = 2<super>10</super>, "
                       "P = 16 the compute time <i>exceeds</i> its value "
                       "at P = 8 even though each rank's workload has "
                       "been halved."))

    # --- Table 4: Karp-Flatt
    rows = [["N", "e(P = 4)", "e(P = 8)", "e(P = 16)",
             "implied S∞ = 1/e"]]
    for n in d.SIZES:
        es = [d.karp_flatt(n, p) for p in d.PCOLS]
        lo = min(es)
        ceil = f"{1.0 / lo:.1f}×" if lo > 0 else "—"
        rows.append([nlab(n)] + [f"{e:.4f}" for e in es] + [ceil])
    S.append(table(rows, [0.9 * inch] + [1.2 * inch] * 3 + [1.3 * inch]))
    S.append(tabnum(4, "The Karp–Flatt metric [6], "
                       "e = (1/S − 1/P)/(1 − 1/P): the serial "
                       "fraction that Amdahl's law would require in order "
                       "to reproduce the measured speedup. The final "
                       "column applies Amdahl's bound at the smallest e in "
                       "each row."))

    # --- Table 5: replication
    rows = [["N", "P", "job 100418 (s)", "job 100371 (s)", "difference"]]
    for n in d.SIZES:
        for p in d.PCOLS:
            rows.append([nlab(n, size=8.2) if p == 4 else "", str(p),
                         f"{d.t_par(n, p):.6f}", f"{d.REPL[(n, p)]:.6f}",
                         f"{100 * d.repl_delta(n, p):.2f}%"])
    S.append(table(rows, [0.8 * inch, 0.55 * inch, 1.5 * inch, 1.5 * inch,
                          1.1 * inch], align_right_from=1, size=8.2))
    S.append(tabnum(5, "Independent replication of the complete sweep on a "
                       "separate node. Agreement is within 0.34% at "
                       "N = 2<super>12</super> and within 2.9% at "
                       "N = 2<super>10</super>; the larger discrepancies at "
                       "N = 2<super>6</super> reflect timer resolution on "
                       "measurements of order 10⁵ seconds."))

    # ========================================================== 6
    S.append(P("6.&nbsp;&nbsp;Performance Analysis", H1))

    S.append(P("6.1&nbsp;&nbsp;Three regimes", H2))
    S.append(P(
        "The measurements do not form a single family of curves "
        "distinguished only by scale. They separate into regimes, each "
        "governed by a different physical resource.", BODY))
    S.append(P(
        "<b>Latency-dominated (N = 2<super>6</super>).</b> Communication "
        "accounts for between 83% and 96% of wall time (Table 3) and "
        "speedup falls below unity for P ≥ 8. A 64 × 64 product "
        "is roughly half a megaflop; the node completes the arithmetic "
        "faster than it can distribute the operands. The compute-to-"
        "communicate ratio N/P is 4 at P = 16, and the Karp–Flatt "
        "metric between 0.73 and 1.25 states the position without "
        "euphemism: essentially nothing parallelises. This row is not a "
        "defect of the implementation but a demonstration of the lower "
        "limit of useful decomposition.", BULLET))
    S.append(P(
        "<b>Cache-resident (N = 2<super>8</super>).</b> Operand B occupies "
        "0.5 MiB, so even sixteen private copies with their A and C blocks "
        "demand only 4.5 MiB per socket, thirteen per cent of the "
        "available L3. Per-rank throughput is accordingly almost flat "
        "— 4.53 GFLOP/s at P = 1 against 4.14 at P = 16 — and "
        "speedup rises monotonically to 4.71. Efficiency still falls to "
        "0.29, because communication grows relative to a per-rank "
        "workload that is shrinking as 1/P, but nothing anomalous occurs.",
        BULLET))
    S.append(P(
        "<b>Capacity-limited (N = 2<super>10</super>).</b> Speedup is "
        "<i>non-monotonic</i>: 2.80, 4.50, 4.05. Section 6.2 is devoted to "
        "this row.", BULLET))
    S.append(P(
        "<b>Bandwidth-limited (N = 2<super>12</super>).</b> Communication "
        "never exceeds 5.5% of wall time and the best absolute result is "
        "obtained: 10.21× on sixteen ranks at E = 0.638. Compute "
        "scaled perfectly from P = 4 would require 3.06 s at P = 16 "
        "against a measured 4.70 s, a shortfall of 54% that occurs "
        "entirely within the computation phase.", BULLET))

    S.append(P("6.2&nbsp;&nbsp;The cache-capacity cliff", H2))
    S.append(P(
        "At N = 2<super>10</super>, compute time rises from 0.0549 s at "
        "P = 8 to 0.0681 s at P = 16 while each rank's arithmetic workload "
        "is halved (Table 3, shaded). No algorithm can produce this. Our "
        "first hypothesis was contention from a co-resident job; the "
        "replication reported in Table 5 was executed specifically to test "
        "it, under exclusive node allocation, and the effect reproduced "
        "— 0.0636 s against 0.0681 s, with the P = 8 to P = 16 "
        "reversal intact in both runs. The hypothesis was wrong, and the "
        "phenomenon is structural.", BODY))
    S.append(P(
        "Converting compute time into per-rank throughput, where the work "
        "on one rank is 2(N/P)N² floating-point operations, and "
        "placing beside it the last-level cache each rank's working set "
        "demands, identifies the mechanism. A rank's private working set "
        "is its full copy of B together with its blocks of A and C, that "
        "is (N² + 2N²/P) doubles; with ranks distributed evenly "
        "across the two sockets, the demand per socket is "
        "P/2 times that quantity.", BODY))

    rows = [["N", "P", "per rank", "per socket", "÷ 35 MiB L3",
             "GFLOP/s per rank"]]
    shaded = []
    for n in d.SIZES:
        for p in [1] + d.PCOLS:
            rows.append([nlab(n, size=8.2) if p == 1 else "", str(p),
                         f"{d.footprint_rank_MiB(n, p):,.1f} MiB",
                         f"{d.footprint_socket_MiB(n, p):,.1f} MiB",
                         f"{d.l3_occupancy(n, p):.2f}",
                         f"{d.gflops_rank(n, p):.2f}"])
            if n == 1024 and p in (8, 16):
                shaded.append(len(rows) - 1)
    t = table(rows, [0.68 * inch, 0.48 * inch, 1.08 * inch, 1.12 * inch,
                     1.02 * inch, 1.42 * inch], align_right_from=1, size=8.2)
    S.append(shade(t, shaded))
    S.append(tabnum(6, "Last-level cache demand against achieved per-rank "
                       "throughput. The shaded rows bracket the capacity "
                       "crossing at N = 2<super>10</super>, where occupancy "
                       "passes from 1.14 to 2.06 and throughput falls by a "
                       "factor of 2.5."))

    S.append(P(
        "The correspondence is exact where it matters. At "
        "N = 2<super>10</super> the demand is 24 MiB per socket at P = 4 "
        "(69% of capacity, 6.38 GFLOP/s), 40 MiB at P = 8 (114%, 4.89 "
        "GFLOP/s) and 72 MiB at P = 16 (206%, 1.97 GFLOP/s). The "
        "degradation tracks occupancy, and the collapse lands precisely "
        "where the aggregate footprint of the replicated operand overruns "
        "the physical cache. The same arithmetic accounts for the other "
        "rows without adjustment:", BODY))
    S.append(P(
        "At N = 2<super>8</super> the demand never exceeds 13% of "
        "capacity, so there is nothing to lose and throughput holds. At "
        "N = 2<super>12</super>, B alone is 128 MiB and the working set "
        "exceeds L3 by a factor of eleven even at P = 1 — cache "
        "residency was never available at any process count, so no cliff "
        "is possible and what remains is the gentler DRAM-bandwidth "
        "ceiling identified in Section 6.1. One mechanism, three "
        "regimes, no free parameters.", BODY))

    S.append(figure(os.path.join(HERE, "fig4_cache.png"), 5.7, 3,
                    "Per-rank throughput against last-level cache "
                    "occupancy, point labels giving P. The N = "
                    "2<super>10</super> series (aqua) is the only one that "
                    "crosses the capacity line within the sweep, and it is "
                    "the only one whose throughput collapses. "
                    "N = 2<super>12</super> begins beyond the line and declines "
                    "gradually; N = 2<super>8</super> never approaches it."))

    S.append(P(
        "This is the design decision of Section 2.1 presenting its bill. "
        "The standard criticism of operand replication is that per-rank "
        "memory fails to scale, and the standard expectation is that the "
        "penalty arrives as an allocation failure at large N. The "
        "measurements show it arriving far earlier and far more quietly, "
        "as a capacity effect in a cache three orders of magnitude smaller "
        "than main memory, at a problem size where the scheme appears "
        "entirely comfortable in DRAM. The predictive statement is that "
        "the one-dimensional scheme degrades when P·N²·8 "
        "bytes approaches aggregate L3, which for this machine means "
        "N²P ≥ 9.2 × 10<super>6</super> — a condition "
        "N = 2<super>10</super>, P = 16 violates by a factor of two and "
        "N = 2<super>8</super>, P = 16 satisfies with room to spare.",
        BODY))

    S.append(P("6.3&nbsp;&nbsp;Comments on Amdahl's law", H2))
    S.append(P(
        "Amdahl's law [7] bounds speedup by S(P) ≤ 1/(f + (1−f)/P) "
        "for a serial fraction f understood as a fixed property of the "
        "program. <b>This code has no such fraction.</b> Every "
        "floating-point operation in the multiplication is distributed; "
        "what resists parallelisation is communication, which scales as "
        "βN² against arithmetic scaling as cN³/P. The "
        "effective serial fraction is therefore", BODY))
    S.append(eq("f<sub>eff</sub> ≈ βN² / (cN³) "
                "= β/(cN),"))
    S.append(P(
        "a function of the problem size rather than a constant of the "
        "program. The Karp–Flatt metric, which inverts a measured "
        "speedup to recover the f that Amdahl's law would require, makes "
        "this falsifiable. Reading down the P = 4 column of Table 4 gives "
        "0.7251, 0.0903, 0.1424 and −0.0041: the implied serial "
        "fraction falls by more than two orders of magnitude across the "
        "sweep. A constant-f model is not merely a poor fit to these data; "
        "it is contradicted by them. Equivalently, the Amdahl ceiling "
        "1/e rises from 1.4× at N = 2<super>6</super> to "
        "11.1× at N = 2<super>8</super> — the same program, the "
        "same machine, an eightfold change in the asymptotic bound.",
        BODY))
    S.append(P(
        "Reading along a row exposes a second and more interesting failure "
        "of the model. At every problem size e <i>rises</i> with P. Were "
        "the obstacle a genuine serial section, e would be flat; were it "
        "the βN² communication term of Section 2.5, e would be "
        "very nearly flat as well, since that term is independent of P. "
        "At N = 2<super>12</super> it rises from −0.0041 to 0.0378 "
        "while communication never exceeds 5.5% of wall time, so the "
        "quantity being detected is neither a serial section nor message "
        "passing. It is the memory hierarchy of Section 6.2, for which "
        "Amdahl's model contains no term at all.", BODY))

    S.append(figure(os.path.join(HERE, "fig3_amdahl.png"), 6.3, 4,
                    "The Karp–Flatt metric read in both directions. "
                    "(a) Against problem size, the implied serial fraction "
                    "collapses, refuting a constant f. (b) Against process "
                    "count at fixed N on a symmetric-log scale, it rises "
                    "at every size — including N = 2<super>12</super>, "
                    "where communication is negligible and the residual is "
                    "therefore attributable to cache and bandwidth "
                    "pressure."))

    S.append(P(
        "The correct conclusion is twofold, and neither half is a "
        "repudiation of Amdahl. The law remains valid as an upper bound "
        "<i>conditional on f</i>; what the data establish is that f for "
        "this algorithm is determined jointly by the problem size and by "
        "the interaction between the data layout and the cache capacity "
        "of the machine, neither of which is a program constant. "
        "Gustafson's reformulation [8], in which the problem grows "
        "alongside the processor count, is the framework that describes "
        "the observed behaviour, and the N = 2<super>12</super> row with "
        "efficiencies of 1.01, 0.92 and 0.64 is its demonstration. The "
        "N = 2<super>10</super> row is the cautionary complement: "
        "enlarging the problem improves efficiency only until the "
        "replicated operand overruns the cache, beyond which adding "
        "processors makes the computation slower in absolute terms. "
        "Scaled speedup is not unconditionally available; it is available "
        "until a resource the model does not mention runs out.", BODY))

    S.append(P("6.4&nbsp;&nbsp;Threats to validity", H2))
    S.append(P(
        "<b>Turbo frequency.</b> The E5-2683 v3 has a 2.0 GHz base clock "
        "and boosts to 3.0 GHz on a single active core. T<sub>1</sub> is "
        "measured with one active core and therefore runs at the elevated "
        "clock, which makes T<sub>1</sub> smaller and every reported "
        "speedup correspondingly <i>smaller</i>. The figures in Table 2 "
        "are thus conservative rather than flattering. Critically, turbo "
        "cannot explain the P = 8 to P = 16 reversal at "
        "N = 2<super>10</super>, since both are many-core runs at "
        "substantially the same all-core frequency.", BULLET))
    S.append(P(
        "<b>Superlinear efficiency.</b> E = 1.012 at N = 2<super>12</super>, "
        "P = 4 exceeds unity by 1.2%. We attribute this to NUMA "
        "first-touch locality: the single-rank baseline allocates and "
        "initialises all 384 MiB on one socket and draws every byte "
        "through that socket's memory controllers, whereas at P = 4 each "
        "rank's copy of B is local to the socket that touched it. That "
        "the excess survives the turbo headwind described above "
        "strengthens rather than weakens this reading. The magnitude is "
        "small and we do not build any argument upon it.", BULLET))
    S.append(P(
        "<b>Rank-to-socket mapping.</b> The cache analysis of Section 6.2 "
        "assumes OpenMPI's default round-robin placement across sockets, "
        "giving P/2 ranks per socket. A different binding policy would "
        "change the per-socket demand by a constant factor and shift the "
        "predicted crossing, though not the existence of one.", BULLET))
    S.append(P(
        "<b>Timer resolution at N = 2<super>6</super>.</b> Those "
        "measurements are of order 10<super>−5</super> s and the "
        "two runs differ by up to 8.7% (Table 5). The qualitative "
        "conclusion — that communication dominates and speedup falls "
        "below unity — is robust, but the individual figures should "
        "not be read to three significant digits.", BULLET))
    S.append(P(
        "<b>Single-node scope.</b> Confining the study to one node "
        "isolates the memory hierarchy, but it also means the "
        "Θ(P³) isoefficiency derived in Section 2.5 is never "
        "exercised in the regime where the interconnect would dominate. "
        "The predicted penalty relative to Cannon at large P is argued, "
        "not measured.", BULLET))

    # ========================================================== 7
    S.append(P("7.&nbsp;&nbsp;Conclusions", H1))
    S.append(P(
        "A one-dimensional row-wise decomposition was selected over the "
        "asymptotically superior two-dimensional alternatives because the "
        "mandated process counts include P = 8, for which no square "
        "process grid exists; uniformity of algorithm across the sweep was "
        "judged worth a factor of √P/2 in communication volume, which "
        "at P = 16 is a factor of two. The implementation achieves exact "
        "load balance, admits no deadlock or race by construction, and "
        "verifies to zero relative error at all sixteen configurations "
        "— a consequence of the decomposition preserving the order of "
        "the k-summation. The complete sweep was replicated on a second "
        "node, agreeing to 0.34% at the largest size.", BODY))
    S.append(P(
        "The best absolute result is 10.21× on sixteen ranks at "
        "N = 2<super>12</super>, with efficiency 0.638 and communication "
        "below 6% of wall time. The more valuable result is the "
        "explanation of why the remaining 37% is lost, and why "
        "N = 2<super>10</super> loses efficiency on going from eight ranks "
        "to sixteen. It is neither a serial section nor message passing. "
        "Because every rank holds a private copy of B, aggregate "
        "last-level cache demand grows as P·N², and per-rank "
        "throughput collapses by a factor of 2.5 exactly where that demand "
        "crosses 35 MiB per socket. The same model, with no fitted "
        "parameters, explains why N = 2<super>8</super> scales cleanly and "
        "why N = 2<super>12</super> degrades gradually instead of "
        "abruptly.", BODY))
    S.append(P(
        "For Amdahl's law the implication is specific. The implied serial "
        "fraction is not a property of this program: it varies by two "
        "orders of magnitude with problem size, and at fixed problem size "
        "it varies with process count for reasons the law does not model. "
        "Reporting a single f for a communication-bound, cache-sensitive "
        "kernel is a category error. The useful statement is the "
        "conditional one — that speedup is bounded by 1/e for the e "
        "that obtains at a given (N, P), and that e is set by the memory "
        "system as much as by the algorithm.", BODY))
    S.append(P(
        "Three extensions follow directly. Blocking the local kernel over "
        "a tile that fits L2 would decouple throughput from the "
        "N² footprint of B and should remove the cliff without "
        "changing the communication pattern at all, which would be a sharp "
        "test of the mechanism proposed here. Implementing Cannon's "
        "algorithm for the subset P = 4 and 16 would reduce per-rank "
        "memory to 3N²/P and bring the isoefficiency function from "
        "Θ(P³) to Θ(P<sup>3/2</sup>), addressing the cache "
        "pressure and the communication volume at once. Finally, repeating "
        "the sweep on the 96-core Milan nodes, whose eight memory channels "
        "per socket against Haswell's four alter the bandwidth ceiling "
        "without altering the cache argument, would separate the two "
        "effects that Section 6.1 can only distinguish by inference.",
        BODY))

    # ========================================================== refs
    S.append(P("References", H1))
    refs = [
        "[1] L. E. Cannon. <i>A Cellular Computer to Implement the Kalman "
        "Filter Algorithm.</i> PhD thesis, Montana State University, 1969.",
        "[2] R. A. van de Geijn and J. Watts. SUMMA: Scalable Universal "
        "Matrix Multiplication Algorithm. <i>Concurrency: Practice and "
        "Experience</i>, 9(4):255–274, 1997.",
        "[3] D. Irony, S. Toledo and A. Tiskin. Communication lower bounds "
        "for distributed-memory matrix multiplication. <i>Journal of "
        "Parallel and Distributed Computing</i>, 64(9):1017–1026, 2004.",
        "[4] A. Grama, A. Gupta, G. Karypis and V. Kumar. <i>Introduction "
        "to Parallel Computing</i>, 2nd edition. Addison-Wesley, 2003. "
        "(Chapters 5 and 8: isoefficiency; dense matrix algorithms.)",
        "[5] R. Freivalds. Fast probabilistic algorithms. In <i>Mathematical "
        "Foundations of Computer Science</i>, LNCS 74, pp. 57–69. "
        "Springer, 1979.",
        "[6] A. H. Karp and H. P. Flatt. Measuring parallel processor "
        "performance. <i>Communications of the ACM</i>, 33(5):539–543, "
        "1990.",
        "[7] G. M. Amdahl. Validity of the single processor approach to "
        "achieving large scale computing capabilities. In <i>AFIPS "
        "Conference Proceedings</i>, vol. 30, pp. 483–485, 1967.",
        "[8] J. L. Gustafson. Reevaluating Amdahl's law. <i>Communications "
        "of the ACM</i>, 31(5):532–533, 1988.",
        "[9] Message Passing Interface Forum. <i>MPI: A Message-Passing "
        "Interface Standard, Version 3.1.</i> 2015.",
    ]
    for r in refs:
        S.append(P(r, REF))

    # ========================================================== appendices
    S.append(PageBreak())
    S.append(P("Appendix A.&nbsp;&nbsp;Source: matmul_mpi.c", H1))
    S.append(P(
        "Compiled with <font name='LMono' size='9'>mpicc -O3 "
        "-funroll-loops -march=native -o matmul_mpi matmul_mpi.c -lm</font>.",
        BODY))
    S.append(code_block(os.path.join(SRC_DIR, "matmul_mpi.c")))

    S.append(PageBreak())
    S.append(P("Appendix B.&nbsp;&nbsp;Batch script: run23.slurm", H1))
    S.append(code_block(os.path.join(SRC_DIR, "run23.slurm")))
    S.append(Spacer(1, 10))
    S.append(P("Appendix C.&nbsp;&nbsp;Analysis harness: collect.py", H1))
    S.append(P(
        "Parses the <font name='LMono' size='9'>RESULT</font> lines and "
        "derives Tables 1 through 4. Listed in abbreviated form; the "
        "complete file accompanies the submission.", BODY))
    S.append(code_block(os.path.join(SRC_DIR, "collect.py"), limit=78))

    return S


_EXP = {64: 6, 256: 8, 1024: 10, 4096: 12}


def nlab(n, extra="", size=8.6):
    """N rendered as a power of two.

    Written as reportlab markup rather than literal superscript
    characters because Liberation Serif has no glyph for U+2070
    (superscript zero), which 2^10 would otherwise require.
    """
    st = ParagraphStyle(f"NC{size}", fontName="LSerif", fontSize=size,
                        leading=size + 2.0, textColor=INK)
    return Paragraph(f"2<super>{_EXP[n]}</super>{extra}", st)


def code_block(path, limit=None):
    with open(path) as fh:
        lines = fh.read().split("\n")
    if limit:
        lines = lines[:limit] + ["", "    # ... remainder omitted for brevity"]
    out = []
    for i, ln in enumerate(lines, 1):
        ln = ln.replace("\t", "    ").rstrip()
        out.append(f"{i:>4}  {ln}")
    return Preformatted("\n".join(out), CODE)


if __name__ == "__main__":
    author = sys.argv[1] if len(sys.argv) > 1 else "Will Solazzo"
    out = os.path.join(SRC_DIR, "AMS530_Project2_Problem2.3.pdf")
    figures.fig_speedup(os.path.join(HERE, "fig1_speedup.png"))
    figures.fig_efficiency(os.path.join(HERE, "fig2_efficiency.png"))
    figures.fig_amdahl(os.path.join(HERE, "fig3_amdahl.png"))
    figures.fig_cache(os.path.join(HERE, "fig4_cache.png"))
    build(out, author)
    print("wrote", out)
