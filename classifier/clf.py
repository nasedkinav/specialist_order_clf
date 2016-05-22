from sklearn.preprocessing import MinMaxScaler, MaxAbsScaler
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, SGDClassifier

CLF_POOL = {
    'naive_bayes': MultinomialNB(),
    'svm': SVC(kernel='rbf', C=1., gamma=.02),
    'logistic_regression': LogisticRegression(),
    'sgd_svm': SGDClassifier(loss='hinge', penalty='l2', alpha=.001, warm_start=True),
    'sgd_logistic_regression': SGDClassifier(loss='log', penalty='elasticnet', alpha=.001, warm_start=True),
}

SCALER_POOL = {
    'min_max': MinMaxScaler(),
    'max_abs': MaxAbsScaler()
}


class Classifier:
    def __init__(self, clf, scaler=None):
        self.train_X = self.train_y = None

        if scaler:
            self.clf = Pipeline([
                ('scaler', scaler),
                ('classifier', clf)
            ])
        else:
            self.clf = clf

    def __str__(self):
        return self.clf.__str__()

    def fit(self, X, y):
        self.train_X, self.train_y = X, y
        self.clf.fit(X, y)

    def predict(self, X):
        return self.clf.predict(X)
