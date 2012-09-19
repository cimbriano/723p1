import FSM
import util

vocabulary = ['panic', 'picnic', 'ace', 'pack', 
'pace', 'traffic', 'lilac', 'ice', 
'spruce', 'frolic', 'lumberjack', 'buckle']

suffixes   = ['', '+ed', '+ing', '+s']

def buildSourceModel(vocabulary, suffixes):
    # we want a language model that accepts anything of the form
    # *   w
    # *   w+s
    fsa = FSM.FSM()
    fsa.setInitialState('start')
    fsa.setFinalState('end')

    # Accepts Words 
    for word in vocabulary:

        # From start state
        # First letter to first letter

        ## TODO - Check that letter is valid word character
        fsa.addEdge('start', word[0], word[0])

        partial_word = word[0]
        word_less_first_letter = word[1:]

        for letter in word_less_first_letter:
            fsa.addEdge(partial_word, partial_word + letter, letter)
            partial_word += letter

        # From last letter state to end state
        # partial_word and word should be equivalent here
        fsa.addEdge(word, 'end', None) 

    for suffix in suffixes:
        if len(suffix) == 0:
            continue

        # From end state to first caharcter of suffix state
        fsa.addEdge('end', suffix[0], suffix[0])

        partial_suffix = suffix[0]
        suffix_less_first_character = suffix[1:]

        for char in suffix_less_first_character:
            fsa.addEdge(partial_suffix, partial_suffix + char, char)
            partial_suffix += char

        fsa.addEdge(suffix, 'end', None)



    # # Accept Words
    # fsa.addEdge('start', 'start', '.')
    # fsa.addEdge('start', 'end', None)

    # # Accepts w + s
    # fsa.addEdge('start', 'plus', '+')
    # fsa.addEdge('plus', 'plus', '.')
    # fsa.addEdge('plus', 'end', None)


    return fsa

def buildChannelModel():
    # this should have exactly the same rules as englishMorph.py!
    fst = FSM.FSM(isTransducer=True)
    fst.setInitialState('start')
    fst.setFinalState('end')

    # we can always get from start to end by consuming non-+
    # characters... to implement this, we transition to a safe state,
    # then consume a bunch of stuff
    fst.addEdge('start', 'safe', '.', '.')
    fst.addEdge('safe',  'safe', '.', '.')
    fst.addEdge('safe',  'safe2', '+', None)
    fst.addEdge('safe2', 'safe2', '.', '.')
    fst.addEdge('safe',  'end',  None, None)
    fst.addEdge('safe2',  'end',  None, None)
    
    # implementation of rule 1
    fst.addEdge('start' , 'rule1' , None, None)   # epsilon transition
    fst.addEdge('rule1' , 'rule1' , '.',  '.')    # accept any character and copy it
    fst.addEdge('rule1' , 'rule1b', 'e',  None)   # remove the e
    fst.addEdge('rule1b', 'rule1c', '+',  None)   # remove the +
    fst.addEdge('rule1c', 'rule1d', 'e',  'e')    # copy an e ...
    fst.addEdge('rule1c', 'rule1d', 'i',  'i')    #  ... or an i
    fst.addEdge('rule1d', 'rule1d', '.',  '.')    # and then copy the remainder
    fst.addEdge('rule1d', 'end' , None, None)   # we're done

    # implementation of rule 2
    fst.addEdge('start' , 'rule2' , '.', '.')     # we need to actually consume something
    fst.addEdge('rule2' , 'rule2' , '.', '.')     # accept any character and copy it
    fst.addEdge('rule2' , 'rule2b', 'e', 'e')     # keep the e
    fst.addEdge('rule2b', 'rule2c', '+', None)    # remove the +
    for i in range(ord('a'), ord('z')):
        c = chr(i)
        if c == 'e' or c == 'i':
            continue
        fst.addEdge('rule2c', 'rule2d', c, c)     # keep anything except e or i
    fst.addEdge('rule2d', 'rule2d', '.', '.')     # keep the rest
    fst.addEdge('rule2d', 'end' , None, None)   # we're done

    # implementation of rule 3
    fst.addEdge('start', 'rule3', None, None)   # Epsilon transition
    fst.addEdge('rule3', 'rule3', '.', '.')     # Consume any character and copy it
    fst.addEdge('rule3', 'rule3a', 'c', 'c')    # Found c (part of 'ck')
    fst.addEdge('rule3a', 'rule3b', '+', 'k')   # Found a k, add plus
    fst.addEdge('rule3b', 'rule3b', '.', '.')   # Consume and produce rest of word

    fst.addEdge('rule3b', 'end', None, None)

    return fst

def simpleTest():
    fsa = buildSourceModel(vocabulary, suffixes)
    fst = buildChannelModel()

    print "==== Trying source model on strings 'lumberjack' ===="
    output = FSM.runFST([fsa], ["lumberjack"])
    print "==== Result: ", str(output), " ===="

    print "==== Trying source model on strings 'buckle' ===="
    output = FSM.runFST([fsa], ["buckle+ed"])
    print "==== Result: ", str(output), " ===="

    print "==== Trying source model on strings 'ace+ed' ===="
    output = FSM.runFST([fsa], ["ace+ed"])
    print "==== Result: ", str(output), " ===="

    print "==== Trying source model on strings 'panic+ing' ===="
    output = FSM.runFST([fsa], ["panic+ing"])
    print "==== Result: ", str(output), " ===="
    
    print "==== Generating random paths for 'aced', using only channel model ===="
    output = FSM.runFST([fst], ["aced"], maxNumPaths=10, randomPaths=True)
    print "==== Result: ", str(output), " ===="

    print "==== Disambiguating a few phrases: aced, panicked, paniced, sprucing ===="
    output = FSM.runFST([fsa,fst], ["aced", "paniced", "panicked", "sprucing", "buckling", "lumberjacked", "buckled"])
    print "==== Result: ", str(output), " ===="

if __name__ == '__main__':
    simpleTest()
