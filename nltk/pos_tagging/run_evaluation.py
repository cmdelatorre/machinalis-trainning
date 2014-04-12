# -*- coding: utf-8 -*-
from baselines import MajorityTagger, MemorizerTagger, NLTKBiGramsWithBackoff
from evaluation import evaluate_tagger
from postagging import CarlitoxTagger

class TaggerAPI(object):
    def __init__(self, train):
        """
        `train` is a list of sentences.
        each sentence is a list of (word, tag).
        word is a string, tag is a string too.
        """

    def tag(self, words):
        """
        `words` is a list of words. Each word is a string.
        """


taggers = [
    #MajorityTagger,
    #MemorizerTagger,
    CarlitoxTagger,
    ]


print
print "{:^50}".format("POS Taggers evaluation")
print "{:^50}".format("======================")
print "    {:<38}{}".format("Tagger", "Accuracy")
print

for tagger in taggers:
    name = tagger.__name__
    accuracy = evaluate_tagger(tagger)
    print "    {:<38}{:>.2f}%".format(name, accuracy * 100)
