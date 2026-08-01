import numpy as np
from sklearn.svm import OneClassSVM

from .base import BaseModel


class OneClassSVMModel(BaseModel):
    def __init__(
        self, name="One-Class SVM", nu=0.01, kernel="rbf", gamma="scale", **kwargs
    ):
        super().__init__(name)
        self.nu = nu
        self.kernel = kernel
        self.gamma = gamma
        self.kwargs = kwargs
        self.model = OneClassSVM(
            nu=self.nu, kernel=self.kernel, gamma=self.gamma, **self.kwargs
        )

    def fit(self, X_train, y_train=None):
        self.model.fit(X_train)

    def score(self, X_test):
        # OCSVM decision_function returns negative for anomalies.
        # Invert it so higher score = more anomalous.
        return -self.model.decision_function(X_test)

    def predict(self, X_test):
        # Returns -1 for anomaly, 1 for normal.
        preds = self.model.predict(X_test)
        return np.where(preds == -1, 1, 0)
