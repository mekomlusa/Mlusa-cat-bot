# DailyCatie - A Telegram Cat Bot
Python telegram bot test. A bot that can send you random cat images of Ben and Rose.

Live on Telegram: check out [@daliycatie_bot](https://t.me/daliycatie_bot) for more details!

*Sister version*: if you do not own a telegram account, check out our [Twitter bot](https://twitter.com/dailycatporn).

Feedback and modifications are welcome. You may use this bot as a starting point to share photos with others.

## Version updates

v1: reply with random cat photos upon receiving the `/catphoto` command. Enable users to provide feedback by the `/comment` function.
Group chat functionality.

v2: users can now decide whether to get a random cat photo push to their ends daily.

* v2.1: bug fixed for turning image push for twice or more times.

* v2.2: bug fixed for daily push automatically turning off due to daily cycling job. Once the daily alert is turned on by an user, it will stay on record until being turned off by the user at a later time.

* v2.3: users can now submit their cat photos through the web interface which directly connects to Cloudinary. ~~See [this repo](https://github.com/mekomlusa/catbot_submit) for more details. (Looks like Cloudinary has a poor support for newer Rails version other than 2.3. I'm still trying to upgrade to Rails 5 soon.)~~

~~v3: multiple uploads are finally supported! The web front end is not working as expected, as it could only show the last picture submitted in sequence. This is a known issue and I do plan on fixing this soon.~~

~~v3.1: Photo management console has its backend engine changed from Ruby to Python. See [this repo](https://github.com/mekomlusa/catbot_submit_flask) for more information.~~

v3: major updates -

* Code upgrades from Python 2.7 to Python 3.6
* Using [context based callback](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Transition-guide-to-Version-12.0) to support Python-telegram-bot framework V.12 and after
* Dockerized option now available. See below for installation instruction.
* Add supports to mysql.

v3.1: Abstract calls to Cloudinary servers. Admin users can now check if new photos have been uploaded to the server and refresh the photo stack through the `pullnewpic` command.

## Deploy the bot

Prerequisite: Please ensure that you have a telegram bot token available, also an active account on [Cloudinary](https://cloudinary.com) is required (and you can upload photos to your Cloudinary account, so that this bot will send random photos from your albums).

### Through Docker (RECOMMEND - NEW!)

1. Clone the whole repository to your environment.

2. Substitute secrets in `env-public.list` to your secrets (Note: `DATABASE_URL` is used by Heroku. Can be left empty there). You may want to set up a MySQL environment beforehand (localhost is fine) so that the script could connect to your designated database.

3. Build the image: `docker build -t "dailycatie:docker" .` (Change `dailycatie:docker` to be your desired tag name, if needed)

4. Run the built image: `docker run --detach --env-file=env-public.list --name your-name-here --net=host dailycatie:docker` (Substitute `your-name-here` to the name of your container)

5. Check the status of the bot via `docker ps`. It should be up and running. Have fun talking with your bot!

### Through Heroku (Assume that an active Heroku account exists)

1. Fork the whole repository to your environment.

2. Change line 23 in `dailyCatie.py` to be "psql" (default value = mysql, which is not supported by Heroku)

2. Set up environment variables via Heroku admin interface or CLI ([instruction](https://devcenter.heroku.com/articles/config-vars))

3. Push the repository to your Heroku account ([Guide](https://devcenter.heroku.com/articles/getting-started-with-python#deploy-the-app)). This repository already have necessary files (e.g. `Procfile`) set up so it should be deployed instantly.

### Through local

Note: only recommend for tempoary testing purpose.

1. Clone the whole repository to your environment.

2. Activate a Python 3.5 and above environment. Install all the required package by: `pip install -r requirements.txt`

3. Run the app: `python dailyCatie.py`.

The bot should be up and running. Hit Ctrl+C (or Command+C) to exit.


## TODO

Inline mode

~~Redesign submission UI~~

~~Allow users to submit multiple cat photos in one shot to the photo library~~

~~Allow users to submit cat photos to the photo library~~

~~Allow users to set whether to receive a random cat photo per day~~
