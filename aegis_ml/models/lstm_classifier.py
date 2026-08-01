import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import logging

logger = logging.getLogger("aegis.phase8.lstm")

class PyTorchLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers):
        super(PyTorchLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # x is (batch, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        # Take the output of the last time step
        last_out = lstm_out[:, -1, :]
        return self.fc(last_out)

class LSTMClassifierModel:
    def __init__(self, input_dim=4, hidden_dim=32, num_layers=2, seq_len=10, epochs=30, lr=0.001):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.seq_len = seq_len
        self.epochs = epochs
        self.lr = lr
        self.model = PyTorchLSTM(input_dim, hidden_dim, num_layers)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.BCELoss()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model.to(self.device)

    def fit(self, X_train, y_train, batch_size=64):
        self.model.train()
        
        # X_train is expected to be (N, seq_len, input_dim)
        X_tensor = torch.FloatTensor(X_train).to(self.device)
        y_tensor = torch.FloatTensor(y_train).view(-1, 1).to(self.device)
        
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item() * batch_X.size(0)
            
            avg_loss = total_loss / len(dataset)
            if (epoch + 1) % 10 == 0:
                logger.info(f"LSTM Epoch {epoch+1}/{self.epochs}, Loss: {avg_loss:.6f}")

    def predict(self, X):
        """
        Returns probability of attack.
        X is expected to be (N, seq_len, input_dim)
        """
        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(self.device)
        with torch.no_grad():
            preds = self.model(X_tensor)
        return preds.cpu().numpy().flatten()
