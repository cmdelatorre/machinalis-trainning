"""
Find 'related' words in a given corpus.

"A B C D E F" --> Window (size = 3):
|_._._|         = "A B C"
  |_._._|       = "B C D"
    |_._._|     = "C D E"
      |_._._|   = "D E F"
        |_._|   = "E F"
          |_|   = "F"
"""
from collections import defaultdict
import nltk
import string


class SlidingWindow(object):
    window_size = 7

    def __init__(self, text):
        self.text = text
        self.text_len = len(text)
        self.words_fdist = nltk.FreqDist(text)
        self.w_ini = None
        self.w_end = None
        self.word_relations = None
        self.relations_len = 0
        self.reset()

    def reset(self):
        self.w_ini = 0
        self.w_end = min(self.w_ini + self.window_size, self.text_len)
        self.word_relations = defaultdict(int)

    def is_empty_window(self):
        return self.w_ini == self.text_len

    def slide_window(self):
        self.w_ini += 1
        self.w_end = min(self.w_ini + self.window_size, self.text_len)

    def get_current_window(self):
        return self.text[self.w_ini: self.w_end]

    def update_related_in_window(self):
        window = self.get_current_window()
        pairs = []
        target_word = window[0]
        for other_word in window[1:]:
            pair = (min(target_word, other_word), max(target_word, other_word))
            self.word_relations[pair] += 1

    def process_relations(self):
        pairs = []
        while not self.is_empty_window():
            self.update_related_in_window()
            self.slide_window()
        self.relations_len = len(self.word_relations.keys())
        return pairs

    def word_prob(self, word):
        return self.words_fdist[word]*1.0 / self.text_len

    def pair_prob(self, pair):
        return self.word_relations[pair]*1.0 / self.relations_len

    def independence_factor(self, pair):
        A = pair[0]
        B = pair[1]
        return abs((self.word_prob(A)*self.word_prob(B)) - self.pair_prob(pair))


if __name__ == '__main__':
    target_corpus = nltk.corpus.brown
    text = target_corpus.words(categories='news')
    stopwords = nltk.corpus.stopwords.words(fileids='english')
    filtered_text = [w.lower()
                     for w in text if (w.lower() not in stopwords and
                                       w.translate(None, string.punctuation))]
    filtered_words = set(filtered_text)
    fdist = nltk.FreqDist(filtered_text)

    slider = SlidingWindow(filtered_text)
    slider.process_relations()
