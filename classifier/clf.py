from sklearn.preprocessing import MinMaxScaler, MaxAbsScaler, StandardScaler
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_selection import SelectFromModel

CLF_POOL = {
    'naive_bayes': MultinomialNB(alpha=.1),
    'svm': SVC(kernel='rbf', C=1., gamma=.02),
    'logistic_regression': LogisticRegression(),
    'sgd_svm': SGDClassifier(loss='hinge', penalty='l2', alpha=.001),
    'sgd_logistic_regression': SGDClassifier(loss='log', penalty='elasticnet', alpha=.001),
}

SELECTOR_POOL = {
    'extra_trees_classifier': ExtraTreesClassifier(n_estimators=50)
}

SCALER_POOL = {
    'min_max': MinMaxScaler(),
    'max_abs': MaxAbsScaler(),
    'standart': StandardScaler(),
}


class Classifier:
    def __init__(self, clf, scaler=None, selector=False):
        if scaler:
            if selector:
                self.clf = Pipeline([
                    ('scaler', scaler),
                    ('selector', SelectFromModel(SELECTOR_POOL['extra_trees_classifier'], .001)),
                    ('classifier', clf)
                ])
            else:
                self.clf = Pipeline([
                    ('scaler', scaler),
                    ('classifier', clf)
                ])
        else:
            if selector:
                self.clf = Pipeline([
                    ('selector', SelectFromModel(SELECTOR_POOL['extra_trees_classifier'], .001)),
                    ('classifier', clf)
                ])
            else:
                self.clf = clf

    def __str__(self):
        if isinstance(self.clf, Pipeline):
            return ', '.join(type(v).__name__ for k, v in self.clf.steps)
        return type(self.clf).__name__

    def fit(self, X, y):
        self.clf.fit(X, y)

    def predict(self, X):
        return self.clf.predict(X)
