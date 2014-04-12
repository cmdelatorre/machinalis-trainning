# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import chain
import nltk


class MajorityTagger(object):
    def __init__(self, train):
        freq = defaultdict(int)
        for sent in train:
            for word, tag in sent:
                freq[tag] += 1
        self.best = max(freq, key=freq.get)

    def tag(self, words):
        return [(word, self.best) for word in words]


class MemorizerTagger(object):
    def __init__(self, train):
        default = MajorityTagger(train).best
        tags_per_word = defaultdict(list)
        for word, tag in chain(*train):
            tags_per_word[word].append(tag)
        self.tags = defaultdict(lambda: default)
        for word, xs in tags_per_word.iteritems():
            freq = defaultdict(int)
            for tag in xs:
                freq[tag] += 1
            self.tags[word] = max(freq, key=freq.get)

    def tag(self, words):
        return [(word, self.tags[word]) for word in words]


class NLTKBiGramsWithBackoff(object):
    def __init__(self, train):
        default = MajorityTagger(train).best
        t0 = nltk.DefaultTagger(default)
        t1 = nltk.UnigramTagger(train, backoff=t0)
        t2 = nltk.BigramTagger(train, backoff=t1)
        self.nltk_tagger = t2

    def tag(self, words):
        return self.nltk_tagger.tag(words)
