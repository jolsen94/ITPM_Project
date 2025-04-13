# website dir is a py package, we can import functions from this dir
from website import create_app
import logging

# Create flask app
app = create_app()

if __name__ == '__main__':
    # run flask app, start the server, debug=True reruns server during testing
    app.run(debug=True)
    # app.run(debug=False)	must turn this to False on production
