import requests
import json
from datetime import datetime, timedelta
import time
import argparse

# Warning: running the command below will load data to FeatureBase from the first Nest device you have access to indefinitely 
# Example cli command:
# python nest_ingest.py --project_id <> --access_token <> --refresh_token <> --client_id <> --client_secret <> --fb_user <> --fb_pw <> --fb_db <>

class nestConn():
    """This class is used to make connection to Nest devices
    """
    def __init__(self, project_id, token, refresh_token=None, client_id=None, client_secret=None):
        self.project_id=project_id
        self.token=token
        self.refresh_token=refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
                            'Content-Type': 'application/json',
                            'Authorization': self.token,
                        }

    def renew_token(self):
        params = (
            ('client_id', self.client_id),
            ('client_secret', self.client_secret),
            ('refresh_token', self.refresh_token),
            ('grant_type', 'refresh_token'),
        )

        response = requests.post('https://www.googleapis.com/oauth2/v4/token', params=params)

        response_json = response.json()
        access_token = response_json['token_type'] + ' ' + response_json['access_token']
        self.token = access_token
        self.headers = {
                            'Content-Type': 'application/json',
                            'Authorization': self.token,
                        }

    def print_token(self):
        print(self.token)


    def get_devices(self):

        url_get_devices = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/' + self.project_id + '/devices'
        response = requests.get(url_get_devices, headers=self.headers)

        return response.json()

    def get_device_stats(self,device_name):
        url_get_device = 'https://smartdevicemanagement.googleapis.com/v1/' + device_name
        iso_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        response = requests.get(url_get_device, headers=self.headers)
        response_json = response.json()
        response_json['req_time'] = iso_date
        #print(response_json)
        return response_json

class featurebaseConn():
    """This class is used to make a connection to FeatureBase Cloud
    """
    def __init__(self, username, password, api_version='v2', database=None):
        self.username=username
        self.password=password
        self.database=database
        self.api_version=api_version
        self.token=self.featurebase_authenticate()

    def featurebase_authenticate(self):
        """A helper function to retrieve an OAuth 2.0 token 'IdToken' which will be
            used to make authenticated HTTP API calls.
        """

        # Send HTTP POST request
        print("Generating new FeatureBase Token")
        response = requests.post(
            url  = "https://id.featurebase.com",
            json = { 'USERNAME' : self.username, 'PASSWORD' : self.password })

        # Check for a HTTP 200 OK status code to confirm success.
        if response.status_code != 200:
            raise Exception(
            "Failed to authenticate. Response from authentication service:\n" +
            response.text)

        # On a successful authentication, you should retrieve the IdToken located in
        # the response at 'AuthenticationResult.IdToken'. This will be needed for any
        # further API calls.
        json  = response.json()

        token = json['AuthenticationResult']['IdToken']
        self.token=token
        return token

    def use_database(self,database):
        self.database=database

    def run_query(self,query):

        url  = f'https://query.featurebase.com/{self.api_version}/databases/{self.database}/query/sql'
        body = query.encode('utf-8')
        headers = {"Content-Type": "text/plain",
            "Authorization": f'Bearer {self.token}'}
        
        response = requests.post(url,headers=headers,data=body)
        if response.status_code != 200:
            print(response.text)

        # Check if schema exists in the response, which indicates success. Exit if error discovered
        try:
            response.json()['schema']
        except KeyError:
            print(f'Some Issue Occurred: \n {response.json()}')
            exit()

        # Check if errors exist in in the response, which indicates errors. Exit if error discovered
        try:
            response.json()['error']
        except KeyError:
            print(f'Query Executed!')
        else:
            print(f'Some Issue Occurred: {response.json()}')
            exit()
        return response.json()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id', type=str, required=True)
    parser.add_argument('--access_token', type=str, required=True)
    parser.add_argument('--refresh_token', type=str, required=False)
    parser.add_argument('--client_id', type=str, required=False)
    parser.add_argument('--client_secret', type=str, required=False)

    parser.add_argument('--fb_user', type=str, required=True)
    parser.add_argument('--fb_pw', type=str, required=True)
    parser.add_argument('--fb_db', type=str, required=True)
    args = parser.parse_args()
    start_time=datetime.now()
    if args.refresh_token:
        conn = nestConn(args.project_id, args.access_token, args.refresh_token, args.client_id, args.client_secret)
    else:
        conn = nestConn(args.project_id, args.access_token)
    conn.renew_token()
    conn.print_token()
    devices = conn.get_devices()
    device_0_name = devices['devices'][0]['name']
    fb_conn = featurebaseConn(args.fb_user,args.fb_pw)
    fb_conn.use_database(args.fb_db)
    
    while 1==1:
        if datetime.now() >= (start_time+ timedelta(minutes=55)) and not(conn.refresh_token is None):
            start_time=datetime.now()
            conn.renew_token()
            conn.print_token()
            fb_conn.featurebase_authenticate()
        device_stats = conn.get_device_stats(device_0_name)
        sql = f'''BULK INSERT INTO gt-nest-thermo (
            _id, 
            display_name,
            device_type,
            device_status,
            fan_timer_mode,
            thermostat_mode,
            eco_mode,
            eco_heat_max_cel,
            eco_cool_min_cel,
            hvac_status,
            temp_dispaly_unit,
            therm_heat_max_cel,
            therm_cool_min_cel,
            ambient_humidity_pct,
            ambient_temp_cel,
            measurement_ts,
            ambient_temp_far
            )
            MAP (
            '$["req_time"]' TIMESTAMP,
            '$["type"]' STRING,
            '$["traits"]["sdm.devices.traits.Humidity"]["ambientHumidityPercent"]' INT,
            '$["traits"]["sdm.devices.traits.Connectivity"]["status"]' STRING,
            '$["traits"]["sdm.devices.traits.Fan"]["timerMode"]' STRING,
            '$["traits"]["sdm.devices.traits.ThermostatMode"]["mode"]' STRING,
            '$["traits"]["sdm.devices.traits.ThermostatEco"]["mode"]' STRING,
            '$["traits"]["sdm.devices.traits.ThermostatEco"]["heatCelsius"]' DECIMAL(6),
            '$["traits"]["sdm.devices.traits.ThermostatEco"]["coolCelsius"]' DECIMAL(6),
            '$["traits"]["sdm.devices.traits.ThermostatHvac"]["status"]' STRING,
            '$["traits"]["sdm.devices.traits.Settings"]["temperatureScale"]' STRING,
            '$["traits"]["sdm.devices.traits.ThermostatTemperatureSetpoint"]["heatCelsius"]' DECIMAL(6),
            '$["traits"]["sdm.devices.traits.ThermostatTemperatureSetpoint"]["coolCelsius"]' DECIMAL(6),
            '$["traits"]["sdm.devices.traits.Temperature"]["ambientTemperatureCelsius"]' DECIMAL(6),
            '$["parentRelations"][0]["displayName"]' STRING
            )
            TRANSFORM(
            CAST(@0 as STRING),
            @14,
            @1,
            @3,
            @4,
            @5,
            @6,
            @7,
            @8,
            @9,
            @10,
            @11,
            @12,
            @2,
            @13,
            @0,
            (@13*9/5)+32)
            FROM '{json.dumps(device_stats)}'
            WITH
            BATCHSIZE 10000
            FORMAT 'NDJSON'
            INPUT 'STREAM'
            ALLOW_MISSING_VALUES;
            '''
        result = fb_conn.run_query(sql)
        print(result)
        # google limits deince info to 10 QPM: https://developers.google.com/nest/device-access/project/limits
        time.sleep(6)

