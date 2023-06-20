# Cron Notion Calendar to ICS

**Currently in development, not ready for production.**

This is a simple script to sync a Notion calendar to an ics file and upload it to a webserver. This is useful if you want to sync your Notion calendar to your phone or other calendar app.

## Setup

### 🐙 Clone this repo

```bash
git clone git@github.com:baptistejouin/cron-notion-ics.git && cd cron-notion-ics
```

### 📦 Install dependencies and create a virtualenv

```bash
# Create a virtualenv (optional)
# install virtualenv: pip install virtualenv
virtualenv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 📠 Complete the config file

- Create a new Notion integration at https://www.notion.so/my-integrations
- Copy the calendar ID from the URL of your calendar
- Copy the URL of your webserver

```bash
cp config.example.json config.json
```

### 🏃‍♂️ Run the script once

```bash
python3 notion-ics.py
```

### ⛳️ Or, add a cronjob (every 5 minutes in this example)

```bash
crontab -e
*/5 * * * * /usr/bin/python3 /path/to/notion-ics/notion-ics.py
```

## License

MIT
