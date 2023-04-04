# nest-base
This repository holds python code to get stats from your personal nest device and load them to a database (FeatueBase)

## Before you being

* Purchase and setup a Nest Thermostat
* Purchase ($5) google developer access and [follow these instructions](https://www.wouternieuwerth.nl/controlling-a-google-nest-thermostat-with-python/)
* Have a [FeatureBase Cloud account](https://cloud.featurebase.com/signup)
* Have ready access to the following:
    * Nest Project ID
    * Nest access token
    * Nest refresh token
    * Nest client ID
    * FeatureBase username (email)
    * FeatureBase password
    * FeatureBase database id

## Setup python env

You need to have a python environment with the proper packages found in the requirements.txt

### Create using conda

```
conda create --name nestbase --file requirements.txt
```


All credit to the above blog for helping me get set up to access my nest's data!

## Running the script

### With a nest refresh token and a specific FeatureBase database
`python nest_ingest.py --project_id <> --access_token <> --refresh_token <> --client_id <> --client_secret <> --fb_user <> --fb_pw <> --fb_db <>`

### With a token that will expire within an hour
`python nest_ingest.py --project_id <> --access_token <> --fb_user <> --fb_pw <> --fb_db <>`