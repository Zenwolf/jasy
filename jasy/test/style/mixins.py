#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine

"""
SUPPORTS

$font{
  font-family: Arial, sans-serif;
  font-size: 15px;
}

h1{
  $font;
  color: blue;
}

h2{
  $font;
  color: red;
}
"""

class Tests(unittest.TestCase):

    def process(self, code):
        callerName = inspect.stack()[1][3][5:]

        tree = Engine.getTree(code, callerName)
        tree = Engine.processTree(tree)
        return Engine.compressTree(tree)

    def test_extend(self):
        self.assertEqual(self.process('''
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font;
              color: blue;
            }

            h2{
              $font;
              color: red;
            }
            '''), '')
        
    def test_after(self):
        return
        self.assertEqual(self.process('''
            h1{
              .cssshadow &{
                text-shadow: 1px;
              }
            }
            '''), '.cssshadow h1{text-shadow:1px;}')

    def test_between(self):
        return
        self.assertEqual(self.process('''
            h1{
              header &:first-child{
                color: red;
              }
            }
            '''), 'header h1:first-child{color:red;}')        




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

