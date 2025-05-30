# ITPM-Project-Complete
This is the complete and working project

TO RUN:
On your terminal, navigate into the directory where main.py is located, and run command `python main.py`
The program was developed on MS Edge, but should work with Firefox and Chrome as well.

DEPENDANCIES:
You can view the required dependancies in the requirements.txt file.

Running the following commands should have pip or conda install the dependancies based on the requirements.txt file.
If you don't want these dependancies globally available on your device, don't forget to create a virtual environment (venv).

FOR PIP:
To create your venv run `python -m venv myenv`. This should create a folder in the directory called venv.
Then, to activate your venv, run `myenv\Scripts\activate`. This might take a moment, but your terminal line should be prefixed with a (venv).
You can run command `pip install -r requirements.txt` to install dependances within your venv.

FOR CONDA:
To create you venv run `conda create --name myenv`.
Then, to activate your venv, run `conda activate myenv`.
You can run command `conda install --file requirements.txt` to install dependances within your venv.

HTML COMPONENTS:
All HTML are located in website/templates. There are two types: Email templates and Main templates. Email templates are HTML files which are used to simulate sending HTML-based emails to users. Main templates are the main HTML files are the front-end resource files for the web app.

IMAGES, CSS & JS, and OTHER EIF:
These reference files are located in the website/static directory. This includes: index.css for styling, index.js for universal javascript, profanity_wordlist.txt for scanning enquiries and replies for profanity (client-based script), suburbs.json for optimising address information and ensure data integrity (client-based script).

Images directory contains the website logo and subfolders for image-required classes: Lounge and TravelAgent.
