import numpy as np
import torch
from torch import nn

from .base import BaseModel


class ExecutionAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.ReLU(),
            nn.Dropout(p=0.1),
            nn.Linear(input_dim // 2, input_dim // 4),
            nn.ReLU(),
            nn.Dropout(p=0.1),
        )
        self.decoder = nn.Sequential(
            nn.Linear(input_dim // 4, input_dim // 2),
            nn.ReLU(),
            nn.Dropout(p=0.1),
            nn.Linear(input_dim // 2, input_dim),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


class PyTorchAutoencoderModel(BaseModel):
    def __init__(self, name="PyTorch Autoencoder", input_dim=80, epochs=50, lr=0.001):
        super().__init__(name)
        self.input_dim = input_dim
        self.epochs = epochs
        self.lr = lr
        self.model = ExecutionAutoencoder(input_dim=input_dim)
        self.threshold = 0.0

    def fit(self, X_train, y_train=None):
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()
        tensor_data = torch.tensor(X_train, dtype=torch.float32)

        for epoch in range(self.epochs):
            self.model.train()
            optimizer.zero_grad()
            output = self.model(tensor_data)
            loss = criterion(output, tensor_data)
            loss.backward()
            optimizer.step()

        self.model.eval()
        with torch.no_grad():
            recon = self.model(tensor_data)
            mses = torch.mean((recon - tensor_data) ** 2, dim=1).numpy()

        # Threshold: mean + 3 std of normal training data
        self.threshold = np.mean(mses) + 3 * np.std(mses)

    def score(self, X_test):
        self.model.eval()
        tensor_data = torch.tensor(X_test, dtype=torch.float32)
        with torch.no_grad():
            recon = self.model(tensor_data)
            mses = torch.mean((recon - tensor_data) ** 2, dim=1).numpy()
        return mses

    def predict(self, X_test):
        scores = self.score(X_test)
        return (scores > self.threshold).astype(int)

    def predict_with_confidence(self, X_test, num_passes=10):
        """
        Runs N stochastic forward passes with dropout enabled (train mode) 
        to estimate confidence using Monte Carlo Dropout.
        Returns:
            mean_mse: Array of mean MSEs across passes
            var_mse: Array of variance across passes
        """
        self.model.train() # Enable dropout
        tensor_data = torch.tensor(X_test, dtype=torch.float32)
        
        all_mses = []
        with torch.no_grad():
            for _ in range(num_passes):
                recon = self.model(tensor_data)
                mses = torch.mean((recon - tensor_data) ** 2, dim=1).numpy()
                all_mses.append(mses)
                
        all_mses = np.array(all_mses) # Shape: (num_passes, num_samples)
        
        mean_mse = np.mean(all_mses, axis=0)
        var_mse = np.var(all_mses, axis=0)
        
        return mean_mse, var_mse

    def save(self, filepath):
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "threshold": self.threshold,
            "input_dim": self.input_dim
        }, filepath)

    @classmethod
    def load(cls, filepath):
        checkpoint = torch.load(filepath)
        instance = cls(input_dim=checkpoint["input_dim"])
        instance.model.load_state_dict(checkpoint["model_state_dict"])
        instance.threshold = checkpoint["threshold"]
        instance.model.eval()
        return instance
