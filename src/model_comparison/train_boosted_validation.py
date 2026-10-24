"""Run one fixed small-tree experiment using the existing evaluation checks."""
from train_logistic_validation import run


if __name__=='__main__':
    # Reuse the same five inputs, targets, ranking rules and checks as the logistic model.
    run(kind='boosted_trees')
