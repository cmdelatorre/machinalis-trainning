# -*- coding: utf-8 -*-
from nltk.corpus import brown
import random


_my_brown = None


def tagger_kfold(dataset, tagger_factory, k=10):
    """
    Does a k-fold accuracy on `dataset` with `tagger_factory`.

    `dataset` is expected to be a list of sentences.
    Each sentence is expected to be a list of (word, tag).

    `tagger_factory(train_sample)` must return a tagger trained on
    `train_sample` and be such that `tagger.tag(sentence)` tags the sentence.

    This method randomly creates k-partitions of the dataset, and k-times
    trains the tagger with k-1 parts and evaluated it with the partition left.
    After all this, it returns the overall accuracy.
    """

    if k <= 1:
        raise ValueError("k argument must be at least 2")

    dataset = list(dataset)
    random.shuffle(dataset)

    miss = 0
    hit = 0
    for i in xrange(k):
        train = [x for j, x in enumerate(dataset) if j % k != i]
        test = [x for j, x in enumerate(dataset) if j % k == i]
        tagger = tagger_factory(train)
        for goldsent in test[:10]:
            testsent = tagger.tag([word for word, _ in goldsent])
            for goldpair, testpair in zip(goldsent, testsent):
                gold_word, gold_tag = goldpair
                test_word, test_tag = testpair
                if gold_word != test_word:
                    raise ValueError("gold and test have different words")

                if gold_tag == test_tag:
                    hit += 1
                else:
                    miss += 1

    return hit / float(hit + miss)


def evaluate_tagger(tagger_factory):
    return tagger_kfold(_get_my_brown(), tagger_factory)


def _get_my_brown():
    global _my_brown
    if _my_brown is None:
        _my_brown = []
        for sent in brown.tagged_sents():
            newsent = []
            for word, tag in sent:
                tag, _, _ = tag.partition("-")
                newsent.append((word, tag))
            _my_brown.append(newsent)
    return _my_brown
