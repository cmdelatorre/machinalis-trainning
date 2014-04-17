from collections import defaultdict, Counter
from itertools import chain
from nltk.metrics.distance import edit_distance

from baselines import MajorityTagger


SUFFIX_LEN = -3  # To be used to define a word's suffix.
SUFFIX_WORD_LEN_THRESHOLD = 5  # Min length of a word to be taken into account for suffix computation.
SUFFIX_SINGLE_TAG_MIN_FREQ = 5

DO_DISTANCE_CHECK = True
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


def trim_tag(tag):
    return tag.split('-')[0]


class ByContextTagger(object):
    """Tag taking into account the word's context."""

    def __init__(self, train):
        # Train a default tagger.
        self.default_tagger = CarlitoxTagger(train)
        # Train this context-aware tagger
        context_next_tags = defaultdict(list)
        words_contexts = defaultdict(lambda: defaultdict(list))
        train_samples = chain(*train)
        # Match each word with all its contexts, and the corresponding tags.
        _, tag_0 = train_samples.next()
        tag_0 = trim_tag(tag_0)
        _, tag_1 = train_samples.next()
        tag_1 = trim_tag(tag_1)
        context = (tag_0, tag_1)
        for word, current_tag in train_samples:
            current_tag = trim_tag(current_tag)
            words_contexts[word][context].append(current_tag)
            #context_next_tags[context].append(current_tag)
            context = (context[1], current_tag)
        # For each word, in a given context, select the most probable tag.
        self.tag_by_context = defaultdict(lambda: defaultdict(str))
        for word, context_tags in words_contexts.iteritems():
            for context, tags_per_context in context_tags.iteritems():
                tags_count = Counter(tags_per_context)
                _, tag = max((n, tag) for (tag, n) in tags_count.iteritems())
                self.tag_by_context[word][context] = tag
        ## For each context select the most probable next tag.
        #self.context_next_tag = defaultdict(str)
        #for context, tags_per_context in context_next_tags.iteritems():
        #    tags_count = Counter(tags_per_context)
        #    _, tag = max((n, tag) for (tag, n) in tags_count.iteritems())
        #    self.context_next_tag[context] = tag

    def tag(self, sentence):
        tagged_sentence = []
        pre_tagged = self.default_tagger.tag(sentence)
        if len(sentence) < 3:
            tagged_sentence = pre_tagged
        else:
            w0, t0 = pre_tagged[0]
            w1, t1 = pre_tagged[1]
            tagged_sentence = [(w0, t0), (w1, t1)]
            context = (t0, t1)
            for word, prliminar_tag in pre_tagged[2:]:
                tag = self.tag_word(word, context) or prliminar_tag
                tagged_sentence.append((word, tag))
                context = (context[1], tag)
        #print "Tagged sentence", tagged_sentence
        return tagged_sentence

    def tag_word(self, word, context):
        t0, t1 = context
        tag = None
        if all(context):
            tag = self.tag_by_context[word][context] or None
            #if not tag:
            #    tag = self.context_next_tag[context] or None
        return tag

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
                if DO_DISTANCE_CHECK:
                    tag = self.closest_word_tag(word)
                tag = tag or self.majority_tagger.best
        return tag

    def closest_word_tag(self, word):
        # Try and use the tag of the most similar word.
        tag = None
        d, closer_word = min((edit_distance(word, w), w) for w in self.wordset)
        if d <= WORD_DISTANCE_THRESHOLD:
            tag = self.tags[closer_word]
        return tag

if __name__ == '__main__':
    from nltk.corpus import brown
    t = ByContextTagger(brown.tagged_sents(categories='news'))
