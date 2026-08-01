import numpy as np
from sklearn.ensemble import IsolationForest

from .base import BaseModel


class IsolationForestModel(BaseModel):
    def __init__(
        self, name="Isolation Forest", contamination=0.01, random_state=42, **kwargs
    ):
        super().__init__(name)
        self.contamination = contamination
        self.random_state = random_state
        self.kwargs = kwargs
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            **self.kwargs
        )

    def fit(self, X_train, y_train=None):
        self.model.fit(X_train)

    def score(self, X_test):
        # Isolation Forest decision_function returns negative values for anomalies.
        # We invert it so higher score = more anomalous (consistent with other models).
        return -self.model.decision_function(X_test)

    def predict(self, X_test):
        # IF returns -1 for anomaly, 1 for normal.
        # We convert to 1 for anomaly, 0 for normal.
        preds = self.model.predict(X_test)
        return np.where(preds == -1, 1, 0)
