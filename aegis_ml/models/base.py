import pickle

from sklearn.base import BaseEstimator


class BaseModel(BaseEstimator):
    """Abstract base class for all anomaly detection models."""

    def __init__(self, name):
        self.name = name
        self.model = None

    def fit(self, X_train, y_train=None):
        """Train the model on normal data."""
        raise NotImplementedError

    def predict(self, X_test):
        """
        Return binary predictions: 0 for normal, 1 for anomaly.
        """
        raise NotImplementedError

    def score(self, X_test):
        """
        Return anomaly scores. Higher score = more anomalous.
        """
        raise NotImplementedError

    def save(self, filepath):
        """Save model to disk."""
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath):
        """Load model from disk."""
        with open(filepath, "rb") as f:
            return pickle.load(f)
