import nltk


class AbstractTagger(object):
    """Interface definition for POS-Tagger classes."""
    
    def train(self, train_sample):
        """
        train_sample is a list of tagged sentences.
        Each sentence is a list of tagged words (tuples).
        
        """
        pass
    
    def tag(self, text):
        pass
    
    @staticmethod
    def taged_words_in_sample(train_sample, limit=None):
        dataset = limit and train_sample[:limit] or train_sample
        return reduce(lambda x, y: x+y, dataset, [])
    
    def tags_in_samples(self, train_sample, limit=None):
        dataset = limit and train_sample[:limit] or train_sample
        return [tag for (word, tag) in self.taged_words_in_sample(train_sample,
                                                                  limit=limit)]
    
    def words_in_samples(self, train_sample, limit=None):
        dataset = limit and train_sample[:limit] or train_sample
        return [word for (word, tag) in self.taged_words_in_sample(train_sample,
                                                                  limit=limit)]
    
class DefaultTagger(AbstractTagger):
    
    def train(self, train_sample):
        tags = self.tags_in_samples(train_sample, limit=2000)
        print len(tags)
        self.most_frequent_tag = nltk.FreqDist(tags).max()
        self.default_tagger = nltk.DefaultTagger(self.most_frequent_tag)
        print 'most_frequent_tag', self.most_frequent_tag
    
    def tag(self, sentence):
        return self.default_tagger.tag(sentence)


class LookupTagger(AbstractTagger):
            
    def train(self, train_sample):
        words_frequency = nltk.FreqDist(self.words_in_samples(train_sample))
        cfd = nltk.ConditionalFreqDist(self.taged_words_in_sample(train_sample))
        most_freq_words = words_frequency.keys()[:100]
        likely_tags = dict((word, cfd[word].max()) for word in most_freq_words)
        self.baseline_tagger = nltk.UnigramTagger(model=likely_tags)
        
    def tag(self, text):
        return self.baseline_tagger.tag(text)


def tagger_factory(train_sample):
    """"""
    tagger = LookupTagger()
    tagger.train(train_sample)
    return tagger


if __name__ == '__main__':
    from nltk.corpus import brown
    from evaluation import evaluate_tagger, _my_brown
    global _my_brown
    
    _my_brown = brown.tagged_sents(categories='humor')
    r = evaluate_tagger(tagger_factory)
    print r
