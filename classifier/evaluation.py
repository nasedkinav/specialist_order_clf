import logging
import numpy as np
import matplotlib.pyplot as plt

from sklearn.cross_validation import StratifiedShuffleSplit
from sklearn.metrics import classification_report, accuracy_score
from sklearn.decomposition import PCA

from clf import MinMaxScaler, SELECTOR_POOL


def evaluate_model(clf, X, y, n_iter=5):
    logger = logging.getLogger(__name__)
    logger.info(str(clf))

    X = np.array(X)
    y = np.array(y)

    cv = StratifiedShuffleSplit(y, n_iter=n_iter, test_size=0.2, random_state=42)

    scores = []
    true_class_0 = []
    true_class_1 = []
    n_iter = 0
    for train_indices, test_indices in cv:
        n_iter += 1
        logger.info("k_fold_%s" % n_iter)

        X_train, y_train = X[train_indices], y[train_indices]
        X_test, y_test = X[test_indices], y[test_indices]

        # fit model
        clf.fit(X_train, y_train)
        # predict
        y_predicted = clf.predict(X_test)

        # accuracy
        score = accuracy_score(y_test, y_predicted)
        scores.append(score)
        logger.info("score: %s" % score)

        # true predictions
        for l in [0, 1]:
            percentage = float(len(set(np.where(y_predicted == l)[0]).intersection(set(np.where(y_test == l)[0])))) / len(np.where(y_test == l)[0])
            if l == 0:
                true_class_0.append(percentage)
            else:
                true_class_1.append(percentage)
            logger.info("true_class_%s: %s" % (l, percentage))

        logger.info("\n%s" % classification_report(y_test, y_predicted, target_names=['failed', 'closed']))

    mean_score = np.mean(np.array(scores))
    mean_0 = np.mean(np.array(true_class_0))
    mean_1 = np.mean(np.array(true_class_1))

    logger.info("mean_score: %s" % mean_score)
    logger.info("mean_true_0: %s" % mean_0)
    logger.info("mean_true_1: %s" % mean_1)

    return mean_score, mean_0, mean_1


def evaluate_data(K, X, y):
    clf = SELECTOR_POOL['extra_trees_classifier']
    clf.fit(np.array(X), np.array(y))

    return zip(K, clf.feature_importances_)


def evaluate_pca(X, y, save_path, scale):
    X = MinMaxScaler().fit_transform(np.array(X)) if scale else np.array(X)

    pca = PCA(n_components=2)
    X = pca.fit_transform(X)

    X = X[:500]
    y = np.array(y)[:500]
    plt.figure()
    for c, i, target_name in zip("rg", [0, 1], ['0', '1']):
        plt.scatter(X[y == i, 0], X[y == i, 1], c=c, label=target_name)
    plt.legend()
    plt.title('PCA (2 components)')
    plt.savefig(save_path)
    plt.close()

    # percentage of variance explained for each components
    return pca.explained_variance_ratio_
