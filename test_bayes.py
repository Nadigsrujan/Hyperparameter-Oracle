from sklearn.svm import SVC
from skopt import BayesSearchCV
from skopt.space import Real
from sklearn.datasets import load_iris
import numpy as np

data = load_iris()
X, y = data.data, data.target

print("Starting BayesSearchCV test...")
try:
    search = BayesSearchCV(
        SVC(),
        {
            'C': Real(0.1, 100, prior='log-uniform'),
            'gamma': Real(0.001, 1, prior='log-uniform')
        },
        n_iter=5,
        cv=3,
        random_state=42
    )
    search.fit(X, y)
    print("BayesSearchCV success!")
except Exception as e:
    print(f"BayesSearchCV failed: {e}")
