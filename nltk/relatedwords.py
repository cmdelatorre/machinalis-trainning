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

    def word_prob(self, word):
        return self.words_fdist[word]*1.0 / self.text_len

    def pair_prob(self, pair):
        return self.word_relations[pair]*1.0 / self.relations_len

    def independence_factor(self, pair):
        A = pair[0]
        B = pair[1]
        return abs((self.word_prob(A)*self.word_prob(B)) - self.pair_prob(pair))


# if __name__ == '__main__':
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


def f(p):
    return (slider.word_prob(p[0]) * slider.word_prob(p[1])) / slider.pair_prob(p)

# Swap order of (relation-value, word-pair) pairs in slider.word_relations
x = [(v, k) for (k, v) in slider.word_relations.items()]
# Compute the metric for all our pairs and order by the given result
z = [(slider.pair_prob(p[1]), p[1]) for p in x]
z.sort(reverse=True)

# Check if I found the nltk.Text collocations
t = nltk.Text(text)
col = t.collocations()  # Cannot assign, so hardcode
col = """per cent; New York; United States; White House; home runs; last week;
San Francisco; last year; Los Angeles; anti-trust laws; Premier Khrushchev;
Kansas City; President Kennedy; years ago; Air Force;
United Nations; New Orleans; High School; Viet Nam; collective bargaining"""
colocs = col.split(';')
colocs = map(lambda w: w.replace('\n', '').strip(), colocs)
print colocs
pair_colocs = [tuple(map(str.lower, w.split())) for w in colocs]
ordered_pair_collocs = [(min(p), max(p)) for p in pair_colocs]
ranked_collocs = [([e[1] for e in z].index(p), f(p), p) for p in ordered_pair_collocs]
ranked_collocs.sort()
print ranked_collocs