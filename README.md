# ESCI evaluation gain mapping — minimal reproduction

The evaluation script released with
[amazon-science/esci-data](https://github.com/amazon-science/esci-data)
assigns Substitute and Complement the wrong relevance gains. This repo
reproduces the defect in about thirty lines, with no dataset download and
no dependencies.

```bash
python3 reproduce.py
```

## What's wrong

`ranking/prepare_trec_eval_files.py` maps ESCI labels to integer relevance
positions:

```python
esci_label2relevance_pos = {
    "E" : 4,
    "S" : 2,
    "C" : 3,
    "I" : 1,
}
```

`ranking/launch-predictions-task1.sh` turns those positions into gains:

```
terrier trec_eval ${QRELS_FILE} ${RES_FILE} -c -J -m 'ndcg.1=0,2=0.01,3=0.1,4=1'
```

Composing the two:

| label | position | resulting gain | paper value |
|---|---|---|---|
| E | 4 | 1.0 | 1.0 |
| S | 2 | **0.01** | 0.1 |
| C | 3 | **0.1** | 0.01 |
| I | 1 | 0.0 | 0.0 |

Substitute — a related product a shopper might reasonably buy — is scored
ten times *lower* than Complement, an accessory. The two are swapped.

`ranking/train.py` in the same repository uses the correct values:

```python
esci_label2gain = {
    'E' : 1.0,
    'S' : 0.1,
    'C' : 0.01,
    'I' : 0.0,
}
```

So the training and evaluation halves of the released recipe disagree with
each other.

## Why it matters

The script's output changes which system wins. `reproduce.py` builds two
rankings of the same candidates — one favouring Substitutes, one favouring
Complements — and scores both under each convention:

```
            ranking                     released   corrected
----------------------------------------------------------------
System A    E > S > S > C > I             0.9832      1.0000
System B    E > C > C > S > I             1.0000      0.9832
----------------------------------------------------------------
Released script picks:   System B
Corrected script picks:  System A
```

On the real Task 1 data the gap is smaller but not negligible. Substitute
is 21.9% of all judgements, and in my own reproduction of the official
baseline the two conventions differ by roughly **0.019–0.030 NDCG** —
measured on the Task 1 candidate pool (`small_version == 1`) with a
held-out split carved from the official training data, at full-list and
@20. Treat that as an order of magnitude rather than a constant: the exact
figure depends on the label distribution of whatever pool you evaluate on.

## Status

The correct mapping is not in dispute. It was posted by a maintainer in
[issue #9](https://github.com/amazon-science/esci-data/issues/9)
(September 2022) as `E=4, S=3, C=2, I=1`, directly alongside the code that
does not match it. The same defect was raised again in
[issue #18](https://github.com/amazon-science/esci-data/issues/18)
(May 2024) and confirmed there.

`prepare_trec_eval_files.py` has had no commit since
[63b7d0e](https://github.com/amazon-science/esci-data/commit/63b7d0e)
(August 2022), so the released script still produces the swapped gains
today.

A fix is open upstream:
[PR #26](https://github.com/amazon-science/esci-data/pull/26).

The mapping was also corrected independently by the authors of the
Shopping Queries Image Dataset paper
([arXiv:2405.15190](https://arxiv.org/abs/2405.15190)), who report a
different baseline NDCG as a result.

## If you use this benchmark

Numbers produced with the released evaluation script are not comparable to
numbers produced with the paper's gain vector. If you are reporting NDCG on
ESCI, state which convention you used. Applying the one-line change in
PR #26 is enough to bring the script in line with `train.py` and the paper.

## What this repo does not claim

`reproduce.py` uses synthetic rankings to show the mapping is inverted and
that it can reorder systems. It does not reproduce the 0.019–0.030 figure —
that requires the full ESCI dataset and a trained baseline. The two claims
are separate: the defect is exact and verifiable from the source, the
magnitude is an empirical measurement on one pool.
