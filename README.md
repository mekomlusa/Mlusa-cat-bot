# DailyCatie - A Telegram Cat Bot
Python telegram bot test. A bot that can send you random cat images of Ben and Rose.

Live on Telegram: check out @daliycatie_bot for more details!

*Sister version*: if you do not own a telegram account, check out our [Twitter bot](https://twitter.com/dailycatporn).

## Version updates

v1: reply with random cat photos upon receiving /catphoto command. Enable users to provide feedback by the /comment function.
Group chat functionality.

v2: users can now decide whether to get a random cat photo push to their ends daily.

* v2.1: bug fixed for turning image push for twice or more times.

* v2.2: bug fixed for daily push automatically turning off due to daily cycling job. Once the daily alert is turned on by an user, it will stay on record until being turned off by the user at a later time.

* v2.3: users can now submit their cat photos through the web interface which directly connects to Cloudinary. ~~See [this repo](https://github.com/mekomlusa/catbot_submit) for more details. (Looks like Cloudinary has a poor support for newer Rails version other than 2.3. I'm still trying to upgrade to Rails 5 soon.)~~

~~v3: multiple uploads are finally supported! The web front end is not working as expected, as it could only show the last picture submitted in sequence. This is a known issue and I do plan on fixing this soon.~~

v3.1: Photo management console has its backend engine changed from Ruby to Python. See [this repo](https://github.com/mekomlusa/catbot_submit_flask) for more information.

## TODO

Inline mode

~~Redesign submission UI~~

~~Allow users to submit multiple cat photos in one shot to the photo library~~

~~Allow users to submit cat photos to the photo library~~

~~Allow users to set whether to receive a random cat photo per day~~
