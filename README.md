---
page_type: sample
description: "App to display Twin Cities Landlord Information"
languages:
  - python
products:
  - azure
  - azure-app-service
---

# Python Django

This is a minimal Django app, without a database, that is deployed to
https://tc-landlords.azurewebsites.net/

Everything interesting is in the `licenses` module.
The file licenses-raw.csv is a direct export of the licence data from this shape file https://opendata.minneapolismn.gov/datasets/active-rental-licenses

Then `transform.py` was used locally to clean the data, create columns for the owners phone, email, name and address in a standard format. These columns are called xPhone, xEmail, xName and xAddress. Once this was done, the Union-Find algorithm was used to efficiently group records that matched on any of these fields. The reuslting data are written back to
`clean_grouped_rental_licenses.csv`, which is deployed as part of the Django app.

The is a very simple Django app that allows you to find all properties that are owned by the same landlord as a given property.

## Changes to Django settings

## Contributing

## Running Locally

Clone this repo

```
git clone https://github.com/michaelaltmann/tc-landlords.git
```

Install python 3.7.x

```
pyenv install 3.7.9
pyenv local 3.7.9
```

Create a python virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install the dependencies

```
pip -r requirements.txt
```

Start the server

```
python manage.py runserver
```

## Deploying

With the Azure commandline installed and authenticated, run

```
az webapp up --name tc-landlords --resource-group michael.altmann_rg_Linux_centralus
```
