# infer_two_levels.py

# Character role inference based on the assumption that
# words assigned to a character could be generated by
# either book-level "themes" or character-level "roles."

# We apply the word "topic" generically to cover both
# themes and roles.

# Uses multiprocessing to divide the work of inference
# across multiple instances of Gibbs sampling; that work
# is done inside the module "gibbs."

import random
import gibbs
import pandas as pd
import numpy as np
from collections import Counter
from multiprocessing import Pool

def get_vocab(vocabpath, maxwords, maxlines):
    '''
    Makes a pass through the data to create a vocabulary.
    The vocabulary is limited to maxwords.
    Also, we only go maxlines into the data file; this allows
    running the script in a small-scale test way on large
    files.

    Returns a vocabulary_list that contains the words in order
    of frequency, and a "lexicon"--a dictionary that rapidly
    hash-maps each word to its index in the list.
    '''

    vocab = Counter()

    sofar = 0

    with open(vocabpath, encoding = 'utf-8') as f:
        for line in f:
            sofar += 1
            if sofar > maxlines:
                break

            fields = line.strip().split()
            charid = fields[0]
            label = fields[1]
            words = fields[2 : ]
            for w in set(words):
                vocab[w] += 1
                # notice adding only once per character

    selected_vocab = vocab.most_common(maxwords)
    with open('selectedvocab.txt', mode = 'w', encoding = 'utf-8') as f:
        for a, b in selected_vocab:
            f.write(str(a) + "\t" + str(b) + '\n')

    vocabulary_list = [x[0] for x in selected_vocab]
    lexicon = dict()
    for idx, val in enumerate(vocabulary_list):
        lexicon[val] = idx

    return vocabulary_list, lexicon

class Character:
    def __init__(self, charname, wordseq, book, numthemes, numroles, numtopics):

        '''
        I organize data hierarchically in "Character" objects that are owned by
        "Books." This entails some overhead; a straightforward Numpy table would
        be more parsimonious. But I hope the Python classes will be immediately
        intellible. For instance, it becomes very easy to "shuffle" the books so
        that different groups are together in each Gibbs pass.

        Each character contains a sequence of wordids -- integers keyed to the
        lexicon -- paired with a sequence of topic assignments for each word
        (topicassigns).

        Remember that "topic" is a generic name covering both book-level "themes"
        and character-level "roles." Both kinds of assignments are listed in
        the topicassigns. But we store the summary statistics separately. The
        Character holds a numpy array summarizing the number of words in each
        possible role; its Book holds a numpy array summarizing the number of words
        in each possible theme.

        The ordinality of a topic determines whether it is a role or theme. Topics 
        up to "numthemes" are themes; beyond that they are interpreted as roles.
        '''

        self.name = charname
        self.numwords = len(wordseq)
        self.wordtypes = np.zeros(self.numwords, dtype = 'int32')
        self.topicassigns = np.zeros(self.numwords, dtype = 'int16')
        self.rolecounts = np.zeros(numroles, dtype = 'int16')
        self.book = book
        self.numthemes = numthemes

        topicroulette = [x for x in range(numtopics)]

        for idx, wordid in enumerate(wordseq):
            self.wordtypes[idx] = wordid
            topic = random.sample(topicroulette, 1)[0]
            self.topicassigns[idx] = topic

            if topic < self.numthemes:
                self.book.themecounts[topic] += 1
            else:
                rolenum = topic - self.numthemes
                self.rolecounts[rolenum] += 1


    def assignword(self, wordidx, newtopicnum):
        '''
        We call this function to reassign a word from
        one topic to another. This requires not only
        changing the topicassign entry, but updating
        the summary statistics in either the Character
        or Book, depending on whether the topic number
        is below numthemes or beyond it (and thus a role).
        '''

        existingtopic = self.topicassigns[wordidx]
        self.topicassigns[wordidx] = newtopicnum

        if existingtopic < self.numthemes:
            self.book.increment_decrement(existingtopic, -1)
        else:
            rolenum = existingtopic - self.numthemes
            self.rolecounts[rolenum] = self.rolecounts[rolenum] - 1

        if newtopicnum < self.numthemes:
            self.book.increment_decrement(newtopicnum, 1)
        else:
            rolenum = newtopicnum - self.numthemes
            self.rolecounts[rolenum] = self.rolecounts[rolenum] + 1

class Book:
    '''
    See the documentation of the Character class, above, for general 
    notes on this data structure. Most importantly a Book object holds
    a list of characters, and summary statistics for book-level themes
    in all the characters that belong to it.
    '''

    def __init__(self, bookname, numthemes, numroles, numtopics):
        self.name = bookname
        self.numthemes = numthemes
        self.themecounts = np.zeros(self.numthemes, dtype = 'int32')

        for i in range(numthemes):
            self.themecounts[i] = 0

        self.characters = []
        self.totalwords = 0

    def accept_character(self, character):

        self.characters.append(character)
        self.totalwords += character.numwords

    def increment_decrement(self, topicnum, change):
        self.themecounts[topicnum] = self.themecounts[topicnum] + change

def load_characters(path, lexicon, numthemes, numroles, maxlines):
    '''
    Initializes the data for LDA:

    path: path to the text file storing character words
    lexicon: dictionary mapping words to wordids
    numthemes: number of book-level "themes"
    numroles: number of character-level "roles"
    maxlines: how far to read into the data file

    Returns a dictionary of books and a topic-word matrix.
    '''

    numtopics = numthemes + numroles

    twmatrix = np.zeros((len(lexicon), numtopics), dtype = 'int64')

    allbooks = dict()

    sofar = 0

    with open(path, encoding = 'utf-8') as f:
        for line in f:
            sofar += 1
            if sofar > maxlines:
                break

            fields = line.strip().split()
            charname = fields[0]

            label = fields[1]
            words = fields[2 : ]
            wordtypes = []

            for w in words:
                if w in lexicon:
                    wordtypes.append(lexicon[w])

            if len(wordtypes) > 32700:
                print("Skipping ", charname, " because too long.")
                # I'm using int16, so numbers above 32767 would be problematic

            elif len(wordtypes) > 9:

                bookname = charname.split('|')[0]

                if bookname not in allbooks:
                    thisbook = Book(bookname, numthemes, numroles, numtopics)
                    allbooks[bookname] = thisbook

                else:
                    thisbook = allbooks[bookname]

                thischaracter = Character(charname, wordtypes, thisbook, numthemes, numroles, numtopics)
                thisbook.accept_character(thischaracter)

                # Build the topic-word matrix.

                for wordtype, topic in zip(thischaracter.wordtypes, thischaracter.topicassigns):
                    twmatrix[wordtype, topic] += 1

    return allbooks, twmatrix

def recreate_matrix(booklist, twmatrix):

    '''
    This function is mostly a failsafe to ensure that
    the topic-word matrix has been updated in a way that
    matches the topic assignments in Books and Characters.

    It doesn't run after every iteration of sampling, but
    does run on the fiftieth iteration, just to check that
    everything is working as we expect.
    '''

    newmat = np.zeros(twmatrix.shape, dtype = 'int64')
    for book in booklist:
        charactercount = 0
        for char in book.characters:
            charactercount += len(char.topicassigns)
            for idx in range(char.numwords):
                w = char.wordtypes[idx]
                z = char.topicassigns[idx]
                newmat[w, z] += 1
        assert book.totalwords ==  charactercount

    assert np.sum(twmatrix) == np.sum(newmat)
    return newmat


def onepass(allbooks, twmatrix, constants):
    '''
    This is getting toward being deprecated, but I'm keeping
    it for now. Basically, a local version of the code in the
    gibbs module for the case where we run sampling without
    multiprocessing.
    '''
    numthemes, numtopics, alpha, beta = constants

    topicroulette  = [int(x) for x in range(numtopics)]

    same = 0
    different = 0

    for bookname, book in allbooks.items():

        topicnormalizer = np.sum(twmatrix, axis = 0)
        # I should technically update this after each iteration
        # but that seems likely to slow things

        for char in book.characters:

            for idx in range(char.numwords):
                w = char.wordtypes[idx]
                z = char.topicassigns[idx]
                themearray = book.themecounts.copy()
                rolearray = char.rolecounts.copy()

                # Decrement the existing topic for this word
                # whether it be a theme or role

                if z < numthemes:
                    themearray[z] = themearray[z] - 1
                else:
                    rolenum = z - numthemes
                    rolearray[rolenum] = rolearray[rolenum] - 1

                rolearray = rolearray / char.numwords
                themearray = themearray / book.totalwords

                topicarray = np.append(themearray, rolearray)

                # Also decrement the wordarray.
                # Note that numpy slices are mutable so this also changes
                # the original twmatrix.

                wordarray = twmatrix[w, : ]
                wordarray[z] -= 1
                topicnormalizer[z] -= 1
                thiswordintopics = (wordarray + beta) / topicnormalizer

                distribution = (topicarray + alpha) * thiswordintopics
                probabilities = distribution / np.sum(distribution)
                choice = np.random.choice(topicroulette, p = probabilities)

                if choice == z:
                    same += 1
                else:
                    different += 1

                char.assignword(idx, choice)
                twmatrix[w, choice] += 1
                topicnormalizer[choice] += 1

    print(different / same)

def print_topicwords(twmatrix, r, vocabulary_list, n):
    '''
    Simply a function that prints the top n words in a topic.
    '''
    alltopiccounts = list(twmatrix[ : , r])
    decorated = [x for x in zip(alltopiccounts, vocabulary_list)]
    decorated.sort(reverse = True)
    topn = [x[1] for x in decorated[0: n]]
    line = str(r) + ': ' + ' | '.join(topn) + "   " + str(np.sum(twmatrix[ : , r]))
    print(line)

def shuffledivide(booklist, n):
    '''
    After each iteration, we reshuffle and divide the
    list of Books into n (numprocesses) chunks.
    '''

    random.shuffle(booklist)
    
    booksequences = [booklist[i::n] for i in range(n)]

    # Note that this will not provide continuous chunks. Instead it will be
    # e.g., [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] ==>
    # [[0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7]]

    return booksequences


if __name__ == '__main__':

    numthemes = 50
    numroles = 50
    numtopics = numthemes + numroles
    numwords = 50000
    maxlines = 100000


    alphamean = 0.001
    beta = 0.1
    alpha = np.array([alphamean] * numtopics)

    constants = (numthemes, numtopics, alpha, beta)

    sourcepath = '../biographies/topicmodel/data/malletficchars.txt'

    vocabulary_list, lexicon = get_vocab(sourcepath,numwords, maxlines)

    allbooks, twmatrix = load_characters(sourcepath, lexicon,
        numthemes, numroles, maxlines)

    numprocesses = 16
    numiterations = 160

    # set this to a higher number for multiprocessing

    if numprocesses > 1:
        booklist = []
        for bookname, book in allbooks.items():
            booklist.append(book)
        booksequences = shuffledivide(booklist, numprocesses)
        print("Sequences: ", len(booksequences))

    for iteration in range(numiterations):
        print("ITERATION: " + str(iteration))

        if iteration % 20 == 0:
            for r in range(numtopics):
                print_topicwords(twmatrix, r, vocabulary_list, 12)
            print()

            if iteration > 99 and iteration % 20 == 0:

                newalpha = np.sum(twmatrix, axis = 0)
                newalpha = newalpha / np.mean(newalpha)
                for idx in range(len(newalpha)):
                    if newalpha[idx] > 2:
                        newalpha[idx] = 2
                    elif newalpha[idx] < 0.5:
                        newalpha[idx] = 0.5
                alpha = newalpha * alphamean
                print(alpha)

                constants = (numthemes, numtopics, alpha, beta)

        if numprocesses > 1:

            quadruplets = []
            random_seeds = [(((i + 1) * (iteration + 1)) % 399) for i in range(numprocesses)]
            print(random_seeds)
            # create a different random state for each process

            for seq, seed in zip(booksequences, random_seeds):
                matrixcopy = twmatrix.copy()
                # deep copy, no data sharing!
                # otherwise parallelism does bad things
                quadruplets.append((seq, matrixcopy, constants, seed))

            print('Multiprocessing ...')
            pool = Pool(processes = numprocesses)
            res = pool.map_async(gibbs.onepass, quadruplets)
            res.wait()
            resultlist = res.get()
            pool.close()
            pool.join()

            booklist = []
            for changematrix, bookseq in resultlist:
                # twmatrix = twmatrix + changematrix
                booklist.extend(bookseq)
                twmatrix = twmatrix + changematrix

            booksequences = shuffledivide(booklist, numprocesses)

            if iteration % 50 == 1:
                altmatrix = recreate_matrix(booklist, twmatrix)
                assert np.array_equal(altmatrix, twmatrix)
                # This should do nothing at all, if my math is working
                # correctly. It's just a sanity check.

        else:

            onepass(allbooks, twmatrix, constants)





