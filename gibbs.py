# gibbs.py

import numpy as np

def onepass(quadruplet):
    booksequence, twmatrix, constants, theseed = quadruplet

    np.random.seed(theseed)

    changematrix = np.zeros(twmatrix.shape, dtype = 'int16')

    numthemes, numtopics, alpha, beta = constants

    same = 0
    different = 0

    topicnormalizer = np.sum(twmatrix, axis = 0, dtype = 'int64')

    for book in booksequence:

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

                chosentopic = np.random.choice(numtopics, size = 1, p = probabilities)

                if chosentopic == z:
                    same += 1
                else:
                    different += 1

                char.assignword(idx, chosentopic)
                twmatrix[w, chosentopic] = twmatrix[w, chosentopic] + 1
                topicnormalizer[chosentopic] = topicnormalizer[chosentopic] + 1

                changematrix[w, z] = changematrix[w, z] - 1
                changematrix[w, chosentopic] = changematrix[w, chosentopic] + 1

                # Note: I used to record changes by keeping a copy of the twmatrix, and
                # subtracting the old and new matrices at the end of the this module.
                # Arguably more efficient computation-wise but it ate memory, since
                # it required two copies of an int32 matrix, and produced a third one
                # by subtraction at the end. This requires only one int32 and one
                # int16 matrix.

    changeratio = (different + 1) / (same + 1)
    del twmatrix, topicnormalizer

    return changematrix, booksequence, changeratio
