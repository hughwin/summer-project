# University of Glasgow 2020 - MScIT Summer Project


#### Get the application running on your system

**You must use** Python 3.5 and have PIP installed. If you are running this on a Mac or Linux, you will require TensorFlow 1.4.1.
- Clone this repo
- Create a virtual environment for the project. 
- In the root folder type `pip install requirements.txt`
- The instance you want to run the bot on must be changed in the settings.py file (`BASE_ADDRESS`)
- You must create a `.env` file containing your Mastodon client key, secret key, and access token. These are loaded when the bot starts, and without them, the bot will not connect to your chosen instance. 
- Start the bot by typing `python main.py`
