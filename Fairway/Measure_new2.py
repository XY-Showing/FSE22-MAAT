import numpy as np
import copy, math
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.neighbors import KDTree
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import accuracy_score,recall_score,precision_score, f1_score,roc_auc_score,matthews_corrcoef
from aif360.metrics import ClassificationMetric
from aif360.datasets import BinaryLabelDataset
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC

def get_classifier(name):
    if name == "lr":
        clf = LogisticRegression()
    elif name == "rf":
        clf = RandomForestClassifier()
    elif name == "svm":
        clf = CalibratedClassifierCV(base_estimator=LinearSVC())
    return clf


def measure_final_score(test_df, clf, model_type, X_train, y_train, X_train_df_copy, y_train_df_copy, X_test, y_test, biased_col):
    clf1 = clf.fit(X_train, y_train)
    clf = get_classifier(model_type)
    clf2 = clf.fit(X_train_df_copy, y_train_df_copy)

    pred_de1 = clf1.predict_proba(X_test)
    pred_de2 = clf2.predict_proba(X_test)

    res = []
    for i in range(len(pred_de1)):
        prob_t = (pred_de1[i][1] + pred_de2[i][1]) / 2
        if prob_t >= 0.5:
            res.append(1)
        else:
            res.append(0)

    y_pred = np.array(res)

    accuracy = accuracy_score(y_test, y_pred)
    recall_macro = recall_score(y_test, y_pred, average='macro')
    precision_macro = precision_score(y_test, y_pred, average='macro')
    f1score_macro = f1_score(y_test, y_pred, average='macro')
    mcc = matthews_corrcoef(y_test, y_pred)

    test_df_copy = copy.deepcopy(test_df)
    test_df_copy['Probability'] = y_pred

    tt1 = BinaryLabelDataset(favorable_label=1, unfavorable_label=0, df=test_df, label_names=['Probability'],
                             protected_attribute_names=[biased_col])
    tt2 = BinaryLabelDataset(favorable_label=1, unfavorable_label=0, df=test_df_copy, label_names=['Probability'],
                             protected_attribute_names=[biased_col])

    classified_metric_pred = ClassificationMetric(tt1, tt2, unprivileged_groups=[{biased_col: 0}], privileged_groups=[{biased_col: 1}])
    spd = abs(classified_metric_pred.statistical_parity_difference())
    aaod = classified_metric_pred.average_abs_odds_difference()
    eod = abs(classified_metric_pred.equal_opportunity_difference())

    return accuracy, recall_macro, precision_macro, f1score_macro, mcc, spd, aaod, eod
