from db_engine import DBConnection
from sklearn import datasets, preprocessing
from sklearn import svm
import numpy as np


class Classifier(object):
    def __init__(self):
        self.db_connection = DBConnection()
        self.iris = datasets.load_iris()
        self.digits = datasets.load_digits()
        self.classifier = svm.SVC(probability=True)

    def train(self, train_data, train_target):
        '''
        Trains SVM classifier based on the feature set acquired in feature_extractor
        Normalises data for optimal results
        Gets class decision and probabilistic result
        :return:
        '''

        X = np.array(train_data)
        X = preprocessing.scale(X)
        self.classifier.fit(X=X, y=train_target)


        coef = self.classifier.coef_  # here the weights of the features will be stored

    def predict(self, target_data):
        '''
        Get predictions for the target data
        :param target_data: array of feature sets for each tweet
        :return:
        '''
        predictions = self.classifier.predict(target_data)
        class_probabilities = self.classifier.predict_proba(target_data)




clf = Classifier()
clf.start()