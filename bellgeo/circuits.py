"""Logical circuits for every scheme and measurement setting.

The builders only call ``h, sdg, cx, measure, barrier`` on the circuit object, so the very
same code builds a ``qiskit.QuantumCircuit`` (``make=lambda nq, nc: QuantumCircuit(nq, nc)``)
and the NumPy ``MiniCircuit`` of ``minisim.py`` that the offline tests use.

Logical qubit / classical bit layout (classical bit i is read from logical qubit i):

    q0 = port A, q1 = port B                  c0, c1 : data bits (always)
    q2 ...        ancillas / intermediates    c2 ... : flag bits or frame bits

Schemes
-------
plain  H(A); CX(A,B)                          the standard Bell circuit, SWAP-routed by Qiskit
zz     plain + ancilla measuring ZZ           flags X/Y-type errors
xx     plain + ancilla measuring XX           flags Z/Y-type errors
zzxx   plain + both ancillas                  flags 12 of the 15 two-qubit Paulis
mbr    measurement-based routing              H(A); CX chain A->n1->...->nk->B on a shortest
                                              path; n_i measured in X; Pauli-frame corrected

Measurement settings: ZZ (none), XX (H on both ports), YY (S^dagger then H on both ports).
All checks are executed BEFORE the basis rotation, and their ancillas are measured in every
setting, so post-selection defines one conditional state for XX, YY and ZZ.
"""

from __future__ import annotations

SCHEMES = ("plain", "zz", "xx", "zzxx", "mbr")
SETTINGS_ORDER = ("XX", "YY", "ZZ")

SCHEME_LABEL = {
    "plain": "no protection",
    "zz": "ZZ parity check",
    "xx": "XX parity check",
    "zzxx": "ZZ+XX double check",
    "mbr": "measurement-based routing",
}


def n_qubits(scheme: str, n_intermediate: int = 0) -> int:
    return {"plain": 2, "zz": 3, "xx": 3, "zzxx": 4}.get(scheme, 2 + n_intermediate)


def build_circuit(scheme: str, setting: str, make, n_intermediate: int = 0):
    """Return (circuit, info). ``make(num_qubits, num_clbits)`` creates an empty circuit."""
    if scheme not in SCHEMES:
        raise ValueError(f"unknown scheme {scheme!r}")
    if setting not in ("XX", "YY", "ZZ"):
        raise ValueError(f"unknown setting {setting!r}")
    if scheme == "mbr" and n_intermediate < 1:
        raise ValueError("mbr needs at least one intermediate qubit (ports not adjacent)")

    nq = n_qubits(scheme, n_intermediate)
    qc = make(nq, nq)
    flag_bits: list[int] = []
    frame_bits: list[int] = []

    # --- Bell preparation ---------------------------------------------------------------
    qc.h(0)
    if scheme == "mbr":
        chain = [0, *range(2, nq), 1]  # A, n1, ..., nk, B
        for u, v in zip(chain[:-1], chain[1:]):
            qc.cx(u, v)
        frame_bits = list(range(2, nq))
    else:
        qc.cx(0, 1)

    # --- checks (ancillas start in |0>) -------------------------------------------------
    if scheme != "plain":
        qc.barrier()
    if scheme in ("zz", "zzxx"):
        anc = 2
        qc.cx(0, anc)
        qc.cx(1, anc)
        flag_bits.append(anc)
    if scheme in ("xx", "zzxx"):
        anc = 2 if scheme == "xx" else 3
        qc.h(anc)
        qc.cx(anc, 0)
        qc.cx(anc, 1)
        qc.h(anc)
        flag_bits.append(anc)
    if scheme != "plain":
        qc.barrier()

    # --- measurement basis --------------------------------------------------------------
    for q in (0, 1):
        if setting == "XX":
            qc.h(q)
        elif setting == "YY":
            qc.sdg(q)
            qc.h(q)
    if scheme == "mbr":
        for q in frame_bits:
            qc.h(q)  # intermediates are measured in the X basis in every setting

    for q in range(nq):
        qc.measure(q, q)

    info = {
        "data_bits": (0, 1),
        "flag_bits": tuple(flag_bits),
        "frame_bits": tuple(frame_bits),
        "n_logical": nq,
    }
    return qc, info
