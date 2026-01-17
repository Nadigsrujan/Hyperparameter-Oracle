from sklearn.datasets import load_iris
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings

# Suppress convergence warnings
warnings.filterwarnings('ignore')

# Load Real Data
data = load_iris()
X_train, X_test, y_train, y_test = train_test_split(data.data, data.target, test_size=0.2, random_state=42)

print("Testing 'Bad' Hyperparameters on Iris (3 classes)...")

# Case 1: Good Params
good_mlp = MLPClassifier(random_state=42, max_iter=200)
good_mlp.fit(X_train, y_train)
acc_good = accuracy_score(y_test, good_mlp.predict(X_test))
print(f"1. Standard MLP: Accuracy = {acc_good:.4f}")

# Case 2: Intentional Failure (High Learning Rate)
# A very high learning rate often causes weights to explode or oscillate, leading to random guessing.
bad_mlp = MLPClassifier(learning_rate_init=10.0, random_state=42, max_iter=200)
bad_mlp.fit(X_train, y_train)
acc_bad = accuracy_score(y_test, bad_mlp.predict(X_test))
print(f"2. MLP with huge Learning Rate (10.0): Accuracy = {acc_bad:.4f}")

# Case 3: Intentional Failure (Tiny network + High Regularization)
bad_mlp_2 = MLPClassifier(hidden_layer_sizes=[1], alpha=100.0, random_state=42, max_iter=200)
bad_mlp_2.fit(X_train, y_train)
acc_bad_2 = accuracy_score(y_test, bad_mlp_2.predict(X_test))
print(f"3. MLP with High Regularization (alpha=100): Accuracy = {acc_bad_2:.4f}")

print("\nConclusion: On a 3-class dataset, if the model fails to learn, accuracy drops to ~0.33 (33%).")
print("This explains why you see dips to ~0.3 in the graph. It is REAL behavior.")
