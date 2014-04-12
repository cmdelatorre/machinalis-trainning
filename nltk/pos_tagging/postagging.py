from collections import defaultdict, Counter
from itertools import chain
from nltk.metrics.distance import edit_distance

from baselines import MajorityTagger


SUFFIX_LEN = -3  # To be used to define a word's suffix.
SUFFIX_WORD_LEN_THRESHOLD = 5  # Min length of a word to be taken into account for suffix computation.
SUFFIX_SINGLE_TAG_MIN_FREQ = 5
WORD_DISTANCE_THRESHOLD = 2

def get_suffix(word):
    return word[SUFFIX_LEN:]

class BySuffixTagger(object):
    delta = 3
    def __init__(self, train):
        """Those suffixes with """
        tags_per_suffix = defaultdict(list)
        for word, tag in chain(*train):
            if len(word) >= SUFFIX_WORD_LEN_THRESHOLD:
                tags_per_suffix[get_suffix(word)].append(tag)

        self.tags = defaultdict(lambda: None)
        for suffix, xs in tags_per_suffix.iteritems():
            freq = Counter(xs)
            tags_ranking = sorted([(v,k) for k,v in freq.items()], reverse=True)
            if len(tags_ranking) < 2:
                # The suffix is always related to the same tag, with frequence f
                f, tag = tags_ranking[0]
                if f > SUFFIX_SINGLE_TAG_MIN_FREQ:
                    self.tags[suffix] = tag
                continue
            (max_n, max_tag), (snd_n, snd_tag) = tags_ranking[:2]
            if max_n > self.delta*snd_n:
                # The most common tag is 3 times more common than the next
                self.tags[suffix] = max_tag

    def tag(self, words):
        return [(word, self.tags[get_suffix(word)]) for word in words]

    
class CarlitoxTagger(object):
    """
    Based on the MemorizerTagger. Instead of using MajorityTagger as default
    (for unknown words), use a custom one.
    
    """
    def __init__(self, train):
        self.majority_tagger = MajorityTagger(train)
        self.suffix_tagger = BySuffixTagger(train)
        self.wordset = set()
        #
        tags_per_word = defaultdict(list)
        for word, tag in chain(*train):
            self.wordset.add(word)
            tags_per_word[word].append(tag)
        self.tags = defaultdict(lambda: None)
        for word, xs in tags_per_word.iteritems():
            freq = defaultdict(int)
            for tag in xs:
                freq[tag] += 1
            self.tags[word] = max(freq, key=freq.get)

    def tag(self, words):
        return [(word, self.choose_tagger(word)) for word in words]

    def choose_tagger(self, word):
        tag = self.tags[word]
        if tag is None:
            tag = self.suffix_tagger.tags[get_suffix(word)]
            if tag is None:
                # Try and use the tag of the most similar word.
                distances = {w: edit_distance(word, w) for w in self.wordset}
                distances = sorted([(distance, w) for w, distance
                                    in distances.items()])
                d, closer_word = distances[0]
                if d <= WORD_DISTANCE_THRESHOLD:
                    tag = self.tags[closer_word]
                else: 
                    tag = self.majority_tagger.best
        return tag
