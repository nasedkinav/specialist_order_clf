import numpy as np
import matplotlib.pyplot as plt

from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.metrics import classification_report, accuracy_score
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.decomposition import PCA

from clf import MinMaxScaler


def evaluate_model(clf, X, y, n_iter=5):
    print clf

    X = np.array(X)
    y = np.array(y)

    cv = StratifiedShuffleSplit(y, n_iter=n_iter, test_size=0.2, random_state=42)
    n_iter = 0
    scores = []
    for train_indices, test_indices in cv:
        n_iter += 1
        print "k_fold_%s" % n_iter

        X_train, y_train = X[train_indices], y[train_indices]
        X_test, y_test = X[test_indices], y[test_indices]

        # fit model
        clf.fit(X_train, y_train)
        # predict
        y_predicted = clf.predict(X_test)

        print classification_report(y_test, y_predicted, target_names=['failed', 'closed'])
        scores.append(accuracy_score(y_test, y_predicted))

    mean_score = np.mean(np.array(scores))
    print "mean_score: %s" % mean_score

    return mean_score


def evaluate_data(K, X, y):
    clf = ExtraTreesClassifier()
    clf.fit(np.array(X), np.array(y))

    return zip(K, clf.feature_importances_)


def evaluate_pca(X, y, save_path):
    X = MinMaxScaler().fit_transform(np.array(X))

    pca = PCA(n_components=2)
    X = pca.fit_transform(X)

    X = X[:500]
    y = np.array(y)[:500]
    plt.figure()
    for c, i, target_name in zip("rg", [0, 1], ['failed', 'closed']):
        plt.scatter(X[y == i, 0], X[y == i, 1], c=c, label=target_name)
    plt.legend()
    plt.title('PCA (2 components)')
    plt.savefig(save_path)
    plt.close()

    # percentage of variance explained for each components
    return pca.explained_variance_ratio_
