import os
import sys
import shutil
import subprocess
import yaml
import requests
import base64
import datetime
import argparse
import pathlib

class IdentimetricsDownloader:
    config = None
    powerschool_authorization_token = None
    errors = ""
    students = []
    staff = []
    total_students = 0
    total_staff = 0
    export_path = os.path.dirname(os.path.abspath(__file__))
    # Load the configuration from the config.yml, config-devel.yml, or config-example.yml file
    # If loading config-example.yml, copy it to config.yml and open the file for editing
    def load_config(self):
            path = os.path.dirname(os.path.abspath(__file__))
            # Check for a config-devel.yml file for development
            if os.path.exists(os.path.join(path,'config-devel.yml')):
                print('Using config-devel.yml')
                configFile = os.path.join(path,'config-devel.yml')
            # Check if config.yml exists, if not, copy from config-example.yml to config.yml and open file
            elif os.path.exists(os.path.join(path,'config.yml')) == False:
                print("Config file does not exist. Copying from config-example.yml")
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

    # PowerSchool Authentication works in two steps
    # First, the client ID and client secret are base64 encoded and sent to the PowerSchool API
    # The API responds with an access token that is used in the headers of subsequent requests
    # The access token will expire so it is re-acquired each time the script is run
    # You can get the client ID and client secret from the PowerSchool plugin page
    def authenticate_with_power_school(self):
        print("Authenticating with PowerSchool")
        try:
            data = self.config["ps_client_id"] + ":" + self.config["ps_client_secret"]
            base64Credentials = base64.b64encode(data.encode('utf-8')).decode('utf-8')

            url = self.config["ps_api_url"] + "/oauth/access_token/"

            # print(url)

            payload = "grant_type=client_credentials"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Authorization": "Basic " + base64Credentials
            }

            response = requests.request("POST", url, data=payload, headers=headers)
            data = response.json()

            #print(data["access_token"])
            self.powerschool_authorization_token = data["access_token"]
            print("Authenticated with PowerSchool")
            # print("token: " + self.powerschoolAuthorizationToken) 
        except Exception as e:
            print("Error authenticating with PowerSchool: " + str(e))
            self.errors += "Error authenticating with PowerSchool: " + str(e) + "\n"   

    # Download students from PowerSchool
    # Uses the powery query provided by the PowerSchool plugin called Identimetrics
    # This plugin is necessary and is always provided in the Tolland Public Schools Github repository
    # The downloaded students are provided in JSON format and stored in the self.students array
    def download_students(self):
        print("Downloading Students")
        try:
            # Each power query has it's own URL as specified in the plugin
            url = self.config["ps_api_url"] + "/ws/schema/query/us.ct.k12.tolland.identimetrics.students.get_import_data?pagesize=0"
            payload = {}
            # The headers include the authorization token
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + self.powerschool_authorization_token
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            data = response.json()
            # A valid query will start with the "record" key
            if ("record" not in data):
                # If no key "record"
                self.errors += "Staff download error: no 'record' key in JSON\n"
                print("Staff download error: no 'record' key in JSON")
                return
            self.students = data["record"]
        except Exception as e:
            print("Error downloading students: " + str(e))
            self.errors += "Error downloading students: " + str(e)  + "\n"

    # Download staff from PowerSchool
    # Uses the powery query provided by the PowerSchool plugin called Identimetrics
    # This plugin is necessary and is always provided in the Tolland Public Schools Github repository
    # The downloaded staff are provided in JSON format and stored in the self.staff array
    def download_staff(self):
        print("Downloading Staff")
        try:
            # Each power query has it's own URL as specified in the plugin
            url = self.config["ps_api_url"] + "/ws/schema/query/us.ct.k12.tolland.identimetrics.staff.get_import_data?pagesize=0"
            payload = {}
            # The headers include the authorization token
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + self.powerschool_authorization_token
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            data = response.json()
            # A valid query will start with the "record" key
            if ("record" not in data):
                # If no key "record"
                self.errors += "Student download error: no 'record' key in JSON\n"
                print("Student download error: no 'record' key in JSON")
                return
            self.staff = data["record"]
        except Exception as e:
            print("Error downloading staff: " + str(e))
            self.errors += "Error downloading staff: " + str(e)  + "\n"

    # Perform any necessary data sanitization, such as removing commas
    def sanitize_data(self, data):
        try:
            for person in data:
                for key in person:
                    if type(person[key]) == str:
                        person[key] = person[key].replace(",", "")
        except Exception as e:
            print("Error sanitizing data: " + str(e))
            self.errors += "Error sanitizing data: " + str(e)  + "\n"

    # If the export path does not exist, create it
    def create_export_path(self):
        if (os.path.exists(self.export_path) == False):
            os.makedirs(self.export_path)
    
    # Write the students to a CSV file in the specified export path
    def write_students(self):        
        try:
            path = os.path.join(self.export_path, 'students.csv')
            print("Writing Students to " + path)
            # If there's a students.csv file, rename it to students + timestamp
            if os.path.exists(path):
                print("Backing up existing students.csv")
                os.rename(path, path + '-' + str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")) + '.csv')
            with open(path, 'w') as f:
                for student in self.students:
                    # Skip students from certain schools defined in config file
                    if student["abbreviation"].upper() in self.config["student_skip_schools"]:
                        print("skipping student from " + student["abbreviation"])
                        continue
                    # PowerSchool excludes the middle name for students where it's not present
                    middle_name = ""
                    if "middle_name" in student:
                        middle_name = student["middle_name"]
                    else:
                        middle_name = ""
                    # Write the student to the file
                    f.write(student["last_name"] + "," + 
                            student["first_name"] + "," + 
                            middle_name + "," + 
                            student["student_number"] + "," + 
                            student["abbreviation"] + "," + 
                            student["grade_level"] + "," + 
                            student["abbreviation"] + "\n")
        except Exception as e:
            print("Error writing students: " + str(e))
            self.errors += "Error writing students: " + str(e)  + "\n"
    
    # Write the staff to a CSV file in the specified export path
    def write_staff(self):        
        try:
            path = os.path.join(self.export_path, 'staff.csv')
            print("Writing Staff to " + path)
            # If there's a staff.csv file, rename it to students + timestamp
            if os.path.exists(path):
                print("Backing up existing staff.csv")
                os.rename(path, path + '-' + str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")) + '.csv')
            with open(path, 'w') as f:
                for staff_member in self.staff:
                    # Skip staff from certain schools defined in config file
                    if staff_member["abbreviation"].upper() in self.config["staff_skip_schools"]:
                        print("skipping staff from " + staff_member["abbreviation"])
                        continue
                    # PowerSchool may exclude the middle name for staff members where it's not present
                    middle_name = ""
                    if "middle_name" in staff_member:
                        middle_name = staff_member["middle_name"]
                    else:
                        middle_name = ""
                    # Get the Identimetrics "Level 2" designation for staff from the config file, fall back to "Staff"
                    staff_level_2 = "Staff"
                    if "staff_level_2" in self.config:
                        staff_level_2 = self.config["staff_level_2"]
                    # Write the student to the file
                    f.write(staff_member["last_name"] + "," + 
                            staff_member["first_name"] + "," + 
                            middle_name + "," + 
                            staff_member["teachernumber"] + "," + 
                            staff_member["abbreviation"] + "," + 
                            staff_level_2 + "," + 
                            staff_member["abbreviation"] + "\n")
        except Exception as e:
            print("Error writing staff: " + str(e))
            self.errors += "Error writing staff: " + str(e)  + "\n"
        
    # Run the Identimetrics Downloader
    def run(self):
        print("Running Identimetrics Downloader")        
        print("Exporting files to directory: " + str(setup_args().output_path))
        self.load_config()
        self.authenticate_with_power_school()
        self.download_students()
        self.download_staff()
        self.create_export_path()
        print("Sanitizing data (removing commas, etc.)")
        self.sanitize_data(self.students)
        self.sanitize_data(self.staff)
        self.write_students()
        self.write_staff()

# Setup the command line arguments
def setup_args():
    parser = argparse.ArgumentParser(description='Identimetrics Downloader')
    parser.add_argument('output_path', type=pathlib.Path, help="Path to output the student and staff export files")
    return parser.parse_args()

# Main function
def main():
    setup_args()
    print("Identimetrics Downloader")
    downloader = IdentimetricsDownloader()
    downloader.export_path = setup_args().output_path
    downloader.run()

if __name__ == "__main__":
   main()