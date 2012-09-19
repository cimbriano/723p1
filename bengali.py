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
                fsa.addEdge(char, second_char, second_char, prob=lm[char][second_char])
    
    return fsa

def buildSegmentChannelModel(words, segmentations):
    fst = FSM.FSM(isTransducer=True, isProbabilistic=True)
    fst.setInitialState('start')
    fst.setFinalState('end')
    ### TODO: YOUR CODE HERE
    #util.raiseNotDefined()
    

    return fst


def fancySouceModel(segmentations):
    raise Exception("fancySouceModel not defined")

def fancyChannelModel(words, segmentations):
    raise Exception("fancyChannelModel not defined")

    
def runTest(trainFile='bengali.train', devFile='bengali.dev', channel=stupidChannelModel, source=bigramSourceModel):
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
    runTest()
