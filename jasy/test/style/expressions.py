#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine
import jasy.core.Permutation as Permutation



class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        permutation = Permutation.Permutation({
            "jasy.engine" : "gecko",
            "jasy.debug" : True
        })

        tree = Engine.getTree(code, callerName)
        tree = Engine.permutateTree(tree, permutation)
        tree = Engine.processTree(tree)

        return Engine.compressTree(tree)


    def test_simple(self):
        self.assertEqual(self.process('''
            h2{
              margin: 20px;
            }
            '''), 'h2{margin:20px;}')



    def test_simple_minus(self):
        self.assertEqual(self.process('''
            h2{
              margin: -20px;
            }
            '''), 'h2{margin:-20px;}')        


    def test_simple_multi(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px 20px 30px;
            }
            '''), 'h2{margin:10px 20px 30px;}')              


    def test_simple_multi_minus(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px - 20px;
            }
            '''), 'h2{margin:-10px;}')            


    def test_simple_multi_plus(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px + 20px;
            }
            '''), 'h2{margin:30px;}')        


    def test_simple_multi_minus_unary(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px -20px;
            }
            '''), 'h2{margin:10px -20px;}')   


    def test_simple_multi_plus_unary(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px +20px;
            }
            '''), 'h2{margin:10px +20px;}')  


    def test_simple_multi_minus_compact(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px-20px;
            }
            '''), 'h2{margin:-10px;}')            


    def test_simple_multi_plus_compact(self):
        self.assertEqual(self.process('''
            h2{
              margin: 10px+20px;
            }
            '''), 'h2{margin:30px;}')    

  




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

