import numpy as np
from sklearn.neighbors import LocalOutlierFactor

from .base import BaseModel


class LOFModel(BaseModel):
    def __init__(
        self, name="Local Outlier Factor", n_neighbors=20, contamination=0.01, **kwargs
    ):
        super().__init__(name)
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        self.kwargs = kwargs
        self.model = LocalOutlierFactor(
            n_neighbors=self.n_neighbors,
            contamination=self.contamination,
            novelty=True,
            **self.kwargs
        )

    def fit(self, X_train, y_train=None):
        # novelty=True must be set to allow prediction on new data
        self.model.fit(X_train)

    def score(self, X_test):
        # Returns negative for anomalies. Invert it.
        return -self.model.decision_function(X_test)

    def predict(self, X_test):
        # Returns -1 for anomaly, 1 for normal.
        preds = self.model.predict(X_test)
        return np.where(preds == -1, 1, 0)
