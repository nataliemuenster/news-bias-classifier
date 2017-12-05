import random
import collections
import math
import sys
import numpy as np
import os
import csv
import string
import util
import time 
import kmeans
from sklearn.metrics import precision_recall_fscore_support
import naive_bayes_optimized as nb_opt
import cPickle as pkl



def readStopWordsFile(fileName):
    contents = []
    f = open(fileName)
    for line in f:
      contents.append(line)
    f.close()
    return ('\n'.join(contents)).split()
stopWords = readStopWordsFile('./english.stop')

def filterStopWords(words):
    """Filters stop words."""
    filtered = []
    for word in words:
      if not word in stopWords and word.strip() != '':
        filtered.append(word)
    return filtered

def createWordCountDict(text):
    uniqueWords = set()
    words = text.translate(None, string.punctuation).lower().split()
    words = filterStopWords(words)
    for word in words:
        uniqueWords.add(word)
    return uniqueWords

def findBestSplit(hingeDict, sourceList, startIndex, dataBySource, liberalSplit, conservativeSplit, wordCountList, devData):
    if startIndex == len(sourceList):
        # TO DO
        # calculate hingeLoss by testing on numDev
        # update hingeDict
        classifier = nb_opt.NaiveBayes()
        print "foundSplit"
        print liberalSplit
        print conservativeSplit

        #Training Phase
        print "start weights"
        for liberalPoint in liberalSplit:
            data = dataBySource[liberalPoint]
            for dataPoint in data:
                exampleNum = dataPoint[0]
                if exampleNum >= 100:
                    continue
                wordCount = wordCountList[exampleNum]
                classifier.train(-1, wordCount, True)
        print "cons"
        for conservativePoint in conservativeSplit:
            data = dataBySource[conservativePoint]
            for dataPoint in data:
                exampleNum = dataPoint[0]
                if exampleNum >= 100:
                    continue
                wordCount = wordCountList[exampleNum]
                classifier.train(1, wordCount, True)
        # Dev Phase 
        numTestCorrect = 0
        total = len(devData)
        for i in range(total):
            dataPoint = devData[i]
            klass = dataPoint[2]
            guess = classifier.classify(wordCountList[dataPoint[0]], True)
            if guess == klass:
                numTestCorrect += 1
        accuracy = float(numTestCorrect) / total
        print "finished"
        print accuracy
        hingeDict[accuracy] = (liberalSplit, conservativeSplit, classifier)
    else:
        newLiberal = list(liberalSplit)
        newLiberal.append(sourceList[startIndex])
        newConservative = list(conservativeSplit)
        findBestSplit(hingeDict, sourceList, startIndex + 1, dataBySource, newLiberal, newConservative, wordCountList, devData)

        newLiberal = list(liberalSplit)
        newConservative = list(conservativeSplit)
        newConservative.append(sourceList[startIndex])
        findBestSplit(hingeDict, sourceList, startIndex + 1, dataBySource, newLiberal, newConservative, wordCountList, devData)


#python unsupervised.py ../cs221-data/read-data/ ./labeled_data.txt 
# Currently Naive Bayes specific, could be generalized
def main(argv):
    if len(argv) < 3:
        print >> sys.stderr, 'Usage: python unsupervised.py <data directory name> <labels file name>'
        sys.exit(1)
    classificationDict = util.createClassDict(argv[2])
    dataList = util.readFiles(argv[1], classificationDict) #if no classificationDict passed in, randomized

    # index in list = exampleNum
    # value at index = wordcountDict
    print "hi"
    labeledData, unlabeledData = util.separateLabeledExamples(dataList)

    
    wordCountList = []
    for value in dataList:
        wordCountList.append(createWordCountDict(value[1]['text']))
    
    with open("./unsupervised_preprocess.txt", "w"):
        pkl.dump(wordCountList, f)


    #print wordCountList[0]

    devLen = len(labeledData) / 2
    devData = []
    testData = []
    random.shuffle(labeledData)
    for i in range(len(labeledData)):
        if i < devLen:
            devData.append(labeledData[i])
        else:
            testData.append(labeledData[i])
    #print devData
    #print testData
    
    print "me"
    # Key = Source
    # Value = List of data points
    sourceList = []
    dataBySource = {}
    for dataPoint in unlabeledData:
        if dataPoint[1]['publication'] in dataBySource:
            dataBySource[dataPoint[1]['publication']].append(dataPoint)
        else:
            sourceList.append(dataPoint[1]['publication'])
            dataBySource[dataPoint[1]['publication']] = [dataPoint]
    # Key = hinge loss. The smallest key will be the one with the lowest global loss and best assignment
    # Value = Tuple ([], [], NaiveBayes()) where the first element is the liberal sources, and the second element is the conservative sources
    hingeDict = {}

    testSourceList = []
    for i in range(3):
        testSourceList.append(sourceList[i])
    print testSourceList
    print sourceList
    # "Dev" Phase
    findBestSplit(hingeDict, testSourceList, 0, dataBySource, [], [], wordCountList, devData)
    print "finished"
    print hingeDict
    # Find best result from "Dev" Phase
    minLoss = float('inf')
    splitTuple = None
    for lossKey in hingeDict:
        if lossKey < minLoss:
            minLoss = lossKey
            splitTuple = hingeDict[lossKey]
    print splitTuple
    print minLoss
    # Test Phase
    numTestCorrect = 0
    total = len(testData)
    for i in range(total):
        dataPoint = testData[i]
        klass = dataPoint[2]
        guess = splitTuple[2].classify(wordCountList[dataPoint[0]], True)
        if guess == klass:
            numTestCorrect += 1
    print "numCorrect: " + str(numTestCorrect) + ' numTotal: ' + str(total) + ' percentage: ' + str(float(numTestCorrect) / total)

if __name__ == '__main__':
    # To speed up, this loop could be pushed inward, so some calculations could be not
    main(sys.argv)