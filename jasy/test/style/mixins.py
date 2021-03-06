#!/usr/bin/env python3

import sys, os, unittest, logging, inspect

# Extend PYTHONPATH with local 'lib' folder
if __name__ == "__main__":
    jasyroot = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir, os.pardir, os.pardir))
    sys.path.insert(0, jasyroot)
    print("Running from %s..." % jasyroot)

import jasy.style.Engine as Engine

"""
SUPPORTS E.G.:

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
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_local_extend(self):
        self.assertEqual(self.process('''
            h1{
              $font{
                font-family: Arial, sans-serif;
                font-size: 15px;
              }

              $font;
              color: blue;

              span {
                $font;
                font-size: 70%;
              }
            }
            '''), '')        
        

    def test_extend_media(self):
        self.assertEqual(self.process('''
            $font{
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            @media screen{
              h1{
                $font;
                color: blue;
              }
            }
            
            h1{
              $font;
              color: black;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:15px;}@media screen{h1{font-family:Arial,sans-serif;font-size:15px;color:blue;}}h1{color:black;}')


    def test_extend_def_as_func(self):
        self.assertEqual(self.process('''
            $font(){
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
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_extend_call(self):
        self.assertEqual(self.process('''
            $font(){
              font-family: Arial, sans-serif;
              font-size: 15px;
            }

            h1{
              $font();
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;font-size:15px;}h1{color:blue;}h2{color:red;}')


    def test_mixin_param(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')


    def test_mixin_param_toomany(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2, 3);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')  


    def test_mixin_param_missing(self):
        import jasy.style.process.Variables as Variables

        def wrapper():
            self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            ''')      

        self.assertRaises(Variables.VariableError, wrapper)


    def test_mixin_default_param(self):
        self.assertEqual(self.process('''
            $font($size=2){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }
            '''), 'h2{font-family:Arial,sans-serif;font-size:30px;}h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{color:red;}')


    def test_mixin_default_param_two_extends(self):
        self.assertEqual(self.process('''
            $font($size=2){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font();
              color: red;
            }

            h3{
              $font();
              color: green;
            }            
            '''), 'h2,h3{font-family:Arial,sans-serif;font-size:30px;}h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{color:red;}h3{color:green;}')        


    def test_mixin_param_transparent_units(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2px);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:30px;color:red;}')   


    def test_mixin_param_mixed_units(self):
        import jasy.style.process.Variables as Variables

        def wrapper():
            self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(3rem);
              color: red;
            }
            ''')      

        self.assertRaises(Variables.VariableError, wrapper)        



    def test_mixin_param_with_compution(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(1+1.5);
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:37.5px;color:red;}')


    def test_mixin_param_with_mixed_compution(self):
        self.assertEqual(self.process('''
            $font($size){
              font-family: Arial, sans-serif;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font( 2 + 3px );
              color: red;
            }
            '''), 'h1{font-family:Arial,sans-serif;font-size:45px;color:blue;}h2{font-family:Arial,sans-serif;font-size:75px;color:red;}')           


    def test_mixin_param_uses_extend(self):
        self.assertEqual(self.process('''
            $arial{
              font-family: Arial, sans-serif;
            }

            $font($size){
              $arial;
              font-size: 15px * $size;
            }

            h1{
              $font(3);
              color: blue;
            }

            h2{
              $font(2);
              color: red;
            }
            '''), 'h1,h2{font-family:Arial,sans-serif;}h1{font-size:45px;color:blue;}h2{font-size:30px;color:red;}')          


    def test_mixin_param_name_conflicts(self):
        self.assertEqual(self.process('''
            $style($size, $color){
              font-size: 15px * $size;
              color: $color;
            }

            h1{
              $color = yellow;
              $style(3, blue);
              background: $color;
            }
            '''), 'h1{font-size:45px;color:blue;background:yellow;}')        


    def test_mixin_param_name_conflicts_default_ignore(self):
        self.assertEqual(self.process('''
            $style($size, $color=red){
              font-size: 15px * $size;
              color: $color;
            }

            h1{
              $color = yellow;
              $style(3, blue);
              background: $color;
            }
            '''), 'h1{font-size:45px;color:blue;background:yellow;}')            


    def test_mixin_param_name_conflicts_default_use(self):
        self.assertEqual(self.process('''
            $style($size, $color=red){
              font-size: 15px * $size;
              color: $color;
            }

            h1{
              $color = yellow;
              $style(3);
              background: $color;
            }
            '''), 'h1{font-size:45px;color:red;background:yellow;}')


    def test_mixin_param_name_default_from_outer(self):
        self.assertEqual(self.process('''
            $titleColor = orange;

            $style($size, $color=$titleColor){
              font-size: 15px * $size;
              color: $color;
              border-bottom: 1px solid $titleColor;
            }

            h1{
              $style(3);
            }
            '''), 'h1{font-size:45px;color:orange;border-bottom:1px solid orange;}')        


    def test_mixin_wrong_place_call(self):
        import jasy.style.parse.Parser as Parser

        def wrapper():
            self.process('''
            $style($color){
              color: $color;
            }

            h1{
              color: $style(red);
            }
            ''')

        self.assertRaises(Parser.SyntaxError, wrapper)        


    def test_mixin_wrong_place_variable(self):
        import jasy.style.process.Variables as Variables

        def wrapper():
            self.process('''
            $style(){
              color: red;
            }

            h1{
              color: $style;
            }
            ''')

        self.assertRaises(Variables.VariableError, wrapper)      


    def test_mixin_content(self):
        self.assertEqual(self.process('''
            $icon(){
              &::before{
                content: "u1929";
                font-family: Icons;
                width: 22px;
                height: 22px;
                display: inline-block;

                @content;
              }
            }

            h1{
              $icon() < {
                margin-right: 2px;
                margin-top: 1px;
              }
            }

            h2{
              $icon();

              color: blue;
            }            
            '''), 'h1::before,h2::before{content:"u1929";font-family:Icons;width:22px;height:22px;display:inline-block;}h1::before{margin-right:2px;margin-top:1px;}h2{color:blue;}')


    def test_mixin_content_double(self):
        self.assertEqual(self.process('''
            $virtual(){
              &::before{
                @content;
              }

              &::after{
                @content;
              }
            }

            h1{
              $virtual() < {
                content: "|";
              }
            }
            '''), 'h1::after{content:"|";}h1::before{content:"|";}')        


    def test_mixin_content_with_param(self):
        self.assertEqual(self.process('''
            $icon(){
              &::before{
                content: "u1929";
                font-family: Icons;
                width: 22px;
                height: 22px;
                display: inline-block;

                @content;
              }
            }

            h1{
              $icon(x) < {
                margin-right: 2px;
                margin-top: 1px;
              }
            }
            '''), 'h1::before{content:"u1929";font-family:Icons;width:22px;height:22px;display:inline-block;margin-right:2px;margin-top:1px;}')


    def test_mixin_content_with_param_double(self):
        self.assertEqual(self.process('''
            $virtual($width, $height){
              &::before{
                width: $width;
                height: $height;

                @content;
              }

              &::after{
                width: $width;
                height: $height;
                
                @content;
              }
            }

            h1{
              $virtual(24px, 30px) < {
                content: "|";
              }
            }
            '''), 'h1::before{width:24px;height:30px;content:"|";}h1::after{width:24px;height:30px;content:"|";}')     


    def test_mixin_local_override(self):
        self.assertEqual(self.process('''
            $icon(){
              &::after{
                content: "u1929";
                font-family: Icons;
              }
            }

            h1{
              $icon($size) {
                margin-right: $size;
                margin-top: $size/2;
              }

              $icon(2px);
            }
            '''), 'h1{margin-right:2px;margin-top:1px;}')


    def test_extend_local_override(self):
        self.assertEqual(self.process('''
            $icon(){
              &::after{
                content: "u1929";
                font-family: Icons;
              }
            }

            h1{
              $icon {
                margin-right: 2px;
                margin-top: 1px;
              }

              $icon;
            }
            '''), 'h1{margin-right:2px;margin-top:1px;}')        


    def test_extend_or_mixin(self):
        self.assertEqual(self.process('''
            $box($color=red) {
              color: $color;
              border: 1px solid $color;
            }

            .errorbox{
              $box;
            }

            .messagebox{
              $box(green);
            }
            .
            '''), '')             


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)   

