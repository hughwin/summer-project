# University of Glasgow 2020 - MScIT Summer Project


### Get the application running on your system

**You must use** Python 3.5 and have PIP installed.
- Clone this repo
- Create a virtual environment for the project. 
- In the root folder type `pip install -r requirements.txt`
- The instance you want to run the bot on must be changed in the settings.py file (`BASE_ADDRESS`) eg. to "https://botsin.space"
- You must create a `.env` file containing your the required environment variables below. These are loaded when the bot starts, and without them, the bot will not connect to your chosen instance. 
- Start the bot by typing `python main.py`

### Environment variables

Name | Required | Default | Description
--- | --- | --- | ---
ACCESS_TOKEN | Yes | N/A | The access token for the Mastodon account that you want the toots to come from
NASA_TOKEN | NO | N/A | The bot toots images obtained from NASA's [APOD](https://api.nasa.gov/) API. The main benefit of this is to show users that the bot is still active, and to advertise it to the userbase - it is not strictly required. Without a key, the bot will simply print an exception to the log. 
gcp_cred.json | Yes | Yes | NA | The bot has some requirment that is perfromed through Google Vision. In order to get this to work properly, you need to get a key from Google, and put the gcp_cred.json in the root of the folder. 

### Heroku

If you are planning on forking this repo with a view to eventually deploying it to Heroku, I would recommend starting your development on the Heroku branch. 