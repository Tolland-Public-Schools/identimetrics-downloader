import os
import sys
import shutil
import subprocess
import yaml
import requests
import http.client
import base64

class IdentimetricsDownloader:
    config = None
    powerschoolAuthorizationToken = None
    errors = ""
    def loadConfig(self):
            path = os.path.dirname(os.path.abspath(__file__))
            # Check for a config-devel.yml file for development
            if os.path.exists(os.path.join(path,'config-devel.yml')):
                print('Using config-devel.yml')
                configFile = os.path.join(path,'config-devel.yml')
            # Check if config.yml exists, if not, copy from config-example.yml to config.yml and open file
            elif os.path.exists(os.path.join(path,'config.yml')) == False:
                print('Config file does not exist. Copying from config-example.yml')
                shutil.copy(os.path.join(path,'config-example.yml'), os.path.join(path,'config.yml'))
                configFile = os.path.join(path,'config.yml')
                print("Opening config file for editing")
                if sys.platform.startswith('darwin'):
                    subprocess.call(('open', configFile))
                elif os.name == 'nt':   # For Windows
                    os.startfile(configFile)
                elif os.name == 'posix':   # For Linux, Unix, etc.
                    subprocess.call(('xdg-open', configFile))
                sys.exit(0)
            # Otherwise, use the standard config.yml
            else:
                configFile = os.path.join(path,'config.yml')
            self.config = yaml.safe_load(open(configFile))
            print("PowerSchool Server: " + str(self.config["ps_api_url"]))

    def authenticateWithPowerSchool(self):
        print("Authenticating with PowerSchool")
        try:
            data = self.config["ps_client_id"] + ":" + self.config["ps_client_secret"]
            base64Credentials = base64.b64encode(data.encode('utf-8')).decode('utf-8')

            url = self.config["ps_api_url"] + "/oauth/access_token/"

            print(url)

            payload = "grant_type=client_credentials"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Authorization": "Basic " + base64Credentials
            }

            response = requests.request("POST", url, data=payload, headers=headers)
            data = response.json()

            #print(data["access_token"])
            self.powerschoolAuthorizationToken = data["access_token"]
            print("Authenticated with PowerSchool")
            print("token: " + self.powerschoolAuthorizationToken) 
        except Exception as e:
            print("Error authenticating with PowerSchool: " + str(e))
            self.errors += "Error authenticating with PowerSchool: " + str(e)        

    # def downloadStudents(self):
    #     conn = http.client.HTTPSConnection(str(self.config["ps_api_url"]))
    #     payload = ""
        
    def run(self):
        print("Running Identimetrics Downloader")
        self.loadConfig()
        self.authenticateWithPowerSchool()
        #self.downloadStudents()

# Main function
def main():
    print("Identimetrics Downloader")
    downloader = IdentimetricsDownloader()
    downloader.run()
if __name__ == "__main__":
   main()