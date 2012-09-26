import FSM
import util
from util import Counter
from FSM import runFST

def readData(filename):
    h = open(filename, 'r')
    words = []
    segmentations = []
    for l in h.readlines():
        a = l.split()
        if len(a) == 1:
            words.append(a[0])
            segmentations.append(None)
        elif len(a) == 2:
            words.append(a[0])
            segmentations.append(a[1])
    return (words, segmentations)

def evaluate(truth, hypothesis):
    I = 0
    T = 0
    H = 0
    for n in range(len(truth)):
        if truth[n] is None: continue
        t = truth[n].split('+')
        allT = {}
        cumSum = 0
        for ti in t:
            cumSum = cumSum + len(ti)
            allT[cumSum] = 1

        h = hypothesis[n].split('+')
        allH = {}
        cumSum = 0
        for hi in h:
            cumSum = cumSum + len(hi)
            allH[cumSum] = 1

        T = T + len(allT) - 1
        H = H + len(allH) - 1
        for i in allT.iterkeys():
            if allH.has_key(i):
                I = I + 1
        I = I - 1
        
    Pre = 1.0
    Rec = 0.0
    Fsc = 0.0
    if I > 0:
        Pre = float(I) / H
        Rec = float(I) / T
        Fsc = 2 * Pre * Rec / (Pre + Rec)
    return (Pre, Rec, Fsc)

def stupidChannelModel(words, segmentations):
    # figure out the character vocabulary
    vocab = Counter()
    for w in words:
        for c in w:
            vocab[c] = vocab[c] + 1

    # build the FST    
    fst = FSM.FSM(isTransducer=True, isProbabilistic=True)
    fst.setInitialState('s')
    fst.setFinalState('s')
    for w in words:
        for c in w:
            fst.addEdge('s', 's', c, c, prob=1.0)    # copy the character
    fst.addEdge('s', 's', '+', None, prob=0.1)       # add a random '+'
    return fst

def stupidSourceModel(segmentations):
    # figure out the character vocabulary
    vocab = Counter()
    for s in segmentations:
        for c in s:
            vocab[c] = vocab[c] + 1
    # convert to probabilities
    vocab.normalize()

    # build the FSA
    fsa = FSM.FSM(isProbabilistic=True)
    fsa.setInitialState('s')
    fsa.setFinalState('s')
    for c,v in vocab.iteritems():
        fsa.addEdge('s', 's', c, prob=v)
    return fsa

def bigramSourceModel(segmentations):
    # compute all bigrams
    lm = {}
    vocab = {}
    vocab['end'] = 1
    for s in segmentations:
        prev = 'start'
        for c in s:
            if not lm.has_key(prev): lm[prev] = Counter()
            lm[prev][c] = lm[prev][c] + 1
            prev = c
            vocab[c] = 1
        if not lm.has_key(prev): lm[prev] = Counter()
        lm[prev]['end'] = lm[prev]['end'] + 1

    # smooth and normalize
    for prev in lm.iterkeys():
        for c in vocab.iterkeys():
            lm[prev][c] = lm[prev][c] + 0.5   # add 0.5 smoothing
        lm[prev].normalize()

    # convert to a FSA
    fsa = FSM.FSM(isProbabilistic=True)
    fsa.setInitialState('start')
    fsa.setFinalState('end')
    
    # Character states in bigram model
    for char in lm['start']:
        fsa.addEdge('start', char, char, lm['start'][char])

    # Transitions between character states or to 'end'
    for char in lm.keys():
        if not char == 'start':
            for second_char in lm[char]:
                if second_char == 'end':
                    fsa.addEdge(char, second_char, None, prob=lm[char][second_char])
                else:
                    fsa.addEdge(char, second_char, second_char, prob=lm[char][second_char])

    
    return fsa

def buildSegmentChannelModel(words, segmentations):
    fst = FSM.FSM(isTransducer=True, isProbabilistic=True)
    fst.setInitialState('start')
    fst.setFinalState('end')

    character_list = {}
    segments_list = {}

    for segmented_words in segmentations:

        # Putting lit of segments into set removes duplicates
        segments = segmented_words.split('+')


        for seg in segments:
            if not segments_list.has_key(seg): 
                segments_list[seg] = 1
                fst.addEdge('start', seg[0], seg[0], seg[0], prob=1)

                partial_seg = seg[0]
                seg_less_first_letter = seg[1:]

                for letter in seg_less_first_letter:
                    if not character_list.has_key(letter): character_list[letter] = 1
                    fst.addEdge(partial_seg, partial_seg + letter, letter, letter, prob=1)
                    partial_seg += letter

            #Add transitions for end of seg to final and back to start for plus
            fst.addEdge(seg, 'end', None, None, prob=1)
            fst.addEdge(seg, 'start', '+', None, prob=1)


    # Low probability edges to account for unseen words
    for letter in character_list.keys():
        fst.addEdge('start', 'start', letter, letter, prob=0.1)
    
    #fst.addEdge('start', 'end', None, None, prob=0.1)
    fst.addEdge('start', 'intermediate', None, None, prob=0.1)
    fst.addEdge('intermediate', 'start', '+', None, prob=0.1)
    fst.addEdge('intermediate', 'end', None, None, prob=0.1)

    return fst


def fancySouceModel(segmentations):

    # compute all trigrams
    lm = {}
    vocab = {}
    vocab['end'] = 1

    for s in segmentations:
        prev2 = 'start'
        prev1 = 'start'

        for c in s:
            if not lm.has_key(prev2):
                lm[prev2] = {}

            if not lm[prev2].has_key(prev1):
                lm[prev2][prev1] = Counter()
            
            # print("prev2 = " + prev2)
            # print("prev1 = " + prev1)
            # print("char  = " + c)

            # print("word = " + s)

            lm[prev2][prev1][c] = lm[prev2][prev1][c] + 1

            # print("Trigram: " + prev2 + " " + prev1 + " " + c)

            prev2 = prev1
            prev1 = c
            vocab[c] = 1


        if not lm.has_key(prev2):
            lm[prev2] = {}
        if not lm[prev2].has_key(prev1):
            lm[prev2][prev1] = Counter()

        lm[prev2][prev1]['end'] = lm[prev2][prev1]['end'] + 1

    vocab['start'] = 1
    vocab['end'] = 1


    # smooth and normalize
    for prev2 in vocab.iterkeys():
        if not lm.has_key(prev2):
            lm[prev2] = {}


        for prev1 in vocab.iterkeys():
            if not lm[prev2].has_key(prev1):
                lm[prev2][prev1] = Counter()

            for c in vocab.iterkeys():
                lm[prev2][prev1][c] = lm[prev2][prev1][c] + 0.5   # add 0.5 smoothing
            lm[prev2][prev1].normalize()

    # convert to a FSA
    fsa = FSM.FSM(isProbabilistic=True)
    fsa.setInitialState('start')
    fsa.setFinalState('end')


    
    # Character states in bigram model
    for first_char in vocab.iterkeys():
        #print("first_char = " + first_char)

        fsa.addEdge('start', first_char, first_char, lm['start']['start'][first_char])

        #print(lm['start'][first_char])

        for second_char in vocab.iterkeys():
            #print("second_char = " + second_char)
            fsa.addEdge(first_char, first_char + second_char, second_char, lm['start'][first_char][second_char])


    # # Transitions between character states or to 'end'
    for first in vocab.iterkeys():
        if not first == 'start':

            for second in vocab.iterkeys():
                if not second == 'start':

                    for c in vocab.iterkeys():
                        if c == 'end':
                            fsa.addEdge(first + second, 'end', None, prob=lm[first][second][c])
                        else:
                            fsa.addEdge(first + second, second + c, c, prob=lm[first][second][c])

    return fsa

def fancyChannelModel(words, segmentations):
    return buildSegmentChannelModel(words, segmentations)
    
    
def runTest(trainFile='bengali.train', devFile='bengali.dev', channel=fancyChannelModel, source=fancySouceModel ):
    (words, segs) = readData(trainFile)
    (wordsDev, segsDev) = readData(devFile)
    fst = channel(words, segs)
    fsa = source(segs)

    preTrainOutput = runFST([fsa, fst], wordsDev, quiet=True)
    for i in range(len(preTrainOutput)):
        if len(preTrainOutput[i]) == 0: preTrainOutput[i] = words[i]
        else:                           preTrainOutput[i] = preTrainOutput[i][0]
    preTrainEval   = evaluate(segsDev, preTrainOutput)
    print 'before training, P/R/F = ', str(preTrainEval)

    fst.trainFST(words, segs)

    postTrainOutput = runFST([fsa, fst], wordsDev, quiet=True)
    for i in range(len(postTrainOutput)):
        if len(postTrainOutput[i]) == 0: postTrainOutput[i] = words[i]
        else:                            postTrainOutput[i] = postTrainOutput[i][0]
    postTrainEval   = evaluate(segsDev, postTrainOutput)
    print 'after  training, P/R/F = ', str(postTrainEval)
    
    return postTrainOutput

def saveOutput(filename, output):
    h = open(filename, 'w')
    for o in output:
        h.write(o)
        h.write('\n')
    h.close()
    

if __name__ == '__main__':
    #runTest()
    
    output = runTest(devFile='bengali.test')
    saveOutput('bengali.test.predictions', output)
