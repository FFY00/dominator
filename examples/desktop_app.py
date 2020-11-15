#!/usr/bin/env python3

import time

import dominator.app


class MyApp(dominator.app.DominatorApp):
    HTML = '''
    <!doctype html>
    <html lang="en">
    <head>
        <title>My App</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    </head>
    <body>
        <div class="container text-center">
            <br><br><br><br><br>
            <h1 id="welcome-text">Welcome to my app!</h1>
        </div>

        <script type="text/javascript">{dominator_javascript}</script>
    </body>
    </html>
    '''

    def __init__(self):
        super().__init__()

        self.body = self.HTML.format(
            # put the dominator javascript in the HTML body
            dominator_javascript=self.dom.javascript,
        )

    def set_welcome_text(self, text):
        self.dom.get_element_by_id('welcome-text')['textContent'].value = text


if __name__ == '__main__':
    app = MyApp()
    app.run()

    while True:
        app.set_welcome_text('Welcome to my app!')
        time.sleep(1)
        app.set_welcome_text('Welcome to my funky app!')
        time.sleep(1)
