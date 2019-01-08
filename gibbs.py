# gibbs.py

import numpy as np
import random

def weighted_choice_sub(weights):
    ''' borrowed from Eli Bendersky'''

    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

def onepass(quadruplet):
    booksequence, twmatrix, constants, theseed = quadruplet

    np.random.seed(theseed)
    random.seed(theseed)

    oldmatrix = twmatrix.copy()

    numthemes, numtopics, alpha, beta = constants

    topicroulette  = [int(x) for x in range(numtopics)]
    zeroes  = 0
    nonzeroes = 0
    same = 0
    different = 0
    zeroprobs = []

    for book in booksequence:

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
                wordarray[z] = wordarray[z] - 1
                topicnormalizer[z] = topicnormalizer[z] - 1
                thiswordintopics = (wordarray + beta) / topicnormalizer

                distribution = (topicarray + alpha) * thiswordintopics
                probabilities = distribution / np.sum(distribution)
                zeroprobs.append(probabilities[0])

                assert len(probabilities) == numtopics

                chosentopic = np.random.choice(numtopics, size = 1, p = probabilities)

                if chosentopic == 0:
                    zeroes += 1
                else:
                    nonzeroes += 1

                if chosentopic == z:
                    same += 1
                else:
                    different += 1

                char.assignword(idx, chosentopic)
                twmatrix[w, chosentopic] = twmatrix[w, chosentopic] + 1
                topicnormalizer[chosentopic] = topicnormalizer[chosentopic] + 1

    print(different / (same + 1))
    if nonzeroes > 0:
        zeropct = zeroes / nonzeroes
    else:
        zeropct = 1

    print(np.mean(zeroprobs), zeropct)
    return twmatrix - oldmatrix, booksequence
