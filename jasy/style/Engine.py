#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Werner
#

import jasy.core.Console as Console 

import jasy.style.tokenize.Tokenizer as Tokenizer

import jasy.style.parse.Parser as Parser
import jasy.style.parse.ScopeScanner as ScopeScanner

import jasy.style.clean.Permutate as Permutate
import jasy.style.clean.Unused as Unused

import jasy.style.process.Mixins as Mixins
import jasy.style.process.Variables as Variables
import jasy.style.process.Flatter as Flatter

import jasy.style.output.Optimization as Optimization
import jasy.style.output.Formatting as Formatting

import jasy.style.output.Compressor as Compressor


def getTokenizer(text, fileId=None):
    """
    Returns a tokenizer for the given file content
    """

    return Tokenizer.Tokenizer(text, fileId, 0)    



def getTree(text, fileId=None):
    """
    Returns a tree of nodes from the given text
    """

    return Parser.parse(text, fileId)


def processTree(tree, fileId=None):
    """
    Applies all relevant modifications to the tree to allow compression to CSS
    """

    # PHASE 1
    # Resolving conditionals
    # self.__resolveConditionals(tree)

    # PHASE 2
    # Trivial cleanups
    ScopeScanner.scan(tree)
    Unused.cleanup(tree)

    # PHASE 3
    # Resolve all mixins
    Mixins.processExtends(tree)
    Mixins.processMixins(tree)
    Mixins.processSelectors(tree)
    Mixins.processExtends(tree)

    # PHASE 4
    # Post mixin cleanups
    ScopeScanner.scan(tree)
    Unused.cleanup(tree)

    # PHASE 5
    # Compute variables
    Variables.compute(tree)

    # PHASE 6
    # Flattening selectors
    Flatter.process(tree)

    # PHASE 7
    # Post scan to remove (hopefully) all variable/mixin access
    ScopeScanner.scan(tree)

    return tree


def compressTree(tree, formatting=None):
    """
    Returns the compressed result from the given tree
    """

    return Compressor.Compressor(formatting).compress(tree)    



def printTokens(text, fileId=None):
    """
    Prints out a structured list of tokens 
    """

    tokenizer = getTokenizer(text, fileId)
    indent = 0

    while tokenizer.get() and not tokenizer.done():
        tokenType = tokenizer.token.type 
        tokenValue = getattr(tokenizer.token, "value", None)
        if tokenType == "left_curly":
            indent += 1
            continue
        elif tokenType == "right_curly":
            indent -= 1
            continue

        if tokenValue is not None:
            Console.info("%s%s: %s" % (indent * "  ", tokenType, tokenValue))
        else:
            Console.info("%s%s" % (indent * "  ", tokenType))


