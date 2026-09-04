"""
Demonstrates the inverted Substitute/Complement mapping in
amazon-science/esci-data ranking/prepare_trec_eval_files.py

No dependencies, no dataset download. Runs in under a second.
"""

import math

# --- What the released code does -------------------------------------------
# ranking/prepare_trec_eval_files.py (unchanged since 63b7d0e, Aug 2022)
RELEASED_LABEL_TO_POS = {"E": 4, "S": 2, "C": 3, "I": 1}

# What it should be, per the maintainer's own table in issue #9
CORRECTED_LABEL_TO_POS = {"E": 4, "S": 3, "C": 2, "I": 1}

# --- How positions become gains --------------------------------------------
# ranking/launch-predictions-task1.sh:
#   terrier trec_eval ... -m 'ndcg.1=0,2=0.01,3=0.1,4=1'
POS_TO_GAIN = {1: 0.0, 2: 0.01, 3: 0.1, 4: 1.0}

# What the paper and ranking/train.py both specify
PAPER_GAINS = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}


def gains(label_to_pos):
    return {lab: POS_TO_GAIN[pos] for lab, pos in label_to_pos.items()}


def ndcg(ranked_labels, label_to_pos):
    """Full-list NDCG, linear gain, log2(i+1) discount — matches trec_eval."""
    g = gains(label_to_pos)

    def dcg(labels):
        return sum(g[lab] / math.log2(i + 2) for i, lab in enumerate(labels))

    ideal = sorted(ranked_labels, key=lambda lab: g[lab], reverse=True)
    idcg = dcg(ideal)
    return dcg(ranked_labels) / idcg if idcg > 0 else 0.0


def rule(char="-", n=64):
    print(char * n)


def main():
    print()
    print("ESCI evaluation gain mapping: released vs. corrected")
    rule("=")

    # 1. Show the mapping disagreement
    released = gains(RELEASED_LABEL_TO_POS)
    corrected = gains(CORRECTED_LABEL_TO_POS)

    print(f"{'label':<8}{'paper / train.py':>18}{'released':>14}{'corrected':>14}")
    rule()
    for lab in ["E", "S", "C", "I"]:
        flag = "" if released[lab] == PAPER_GAINS[lab] else "   <-- wrong"
        print(f"{lab:<8}{PAPER_GAINS[lab]:>18}{released[lab]:>14}"
              f"{corrected[lab]:>14}{flag}")
    rule()
    print("Substitute and Complement are swapped in the released script.")
    print("train.py in the same repo uses the paper values.")
    print()

    # 2. Show it changes ranking decisions
    print("Effect on a ranking comparison")
    rule("=")

    # Two systems ranking the same 4 candidates for one query.
    # A puts Substitutes on top; B puts Complements on top.
    system_a = ["E", "S", "S", "C", "I"]
    system_b = ["E", "C", "C", "S", "I"]

    print(f"{'':<12}{'ranking':<24}{'released':>12}{'corrected':>12}")
    rule()
    for name, order in [("System A", system_a), ("System B", system_b)]:
        r = ndcg(order, RELEASED_LABEL_TO_POS)
        c = ndcg(order, CORRECTED_LABEL_TO_POS)
        print(f"{name:<12}{' > '.join(order):<24}{r:>12.4f}{c:>12.4f}")
    rule()

    winner_released = "A" if ndcg(system_a, RELEASED_LABEL_TO_POS) > ndcg(
        system_b, RELEASED_LABEL_TO_POS) else "B"
    winner_corrected = "A" if ndcg(system_a, CORRECTED_LABEL_TO_POS) > ndcg(
        system_b, CORRECTED_LABEL_TO_POS) else "B"

    print(f"Released script picks:   System {winner_released}")
    print(f"Corrected script picks:  System {winner_corrected}")
    print()
    if winner_released != winner_corrected:
        print("The two conventions disagree on which system is better.")
    print()


if __name__ == "__main__":
    main()
