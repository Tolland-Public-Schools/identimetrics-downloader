# identimetrics-downloader
Download staff and student data from the PowerSchool Identimetrics Plugins for nightly uploads.

## Usage:

On first run, _internal/config-example.yml will be copied to _internal/config.yml and opened in your operating system's default text editor. Be sure to configure for your setup before running again.

### Windows:
identimetricsdownloader.exe [path to export folder]  
Example: identimetricsdownloader.exe c:\users\public\

#### Scheduled Task
If running as a Windows scheduled task, make sure to give whichever user the job will be running as "Log on as a batch job" permissions under Security Settings > Local Policies > User Rights Assignment in the Local Security Policy manager.  
Use the 'Add arguments (optional)' box to specify the export folder.

### Linux:
./identimetricsdownloader [path to export folder]  
Example: ./identimetricsdownloader ~/

#### Icon created by Tolland High School alum Ame Thammavong
![image info](./identimetrics_downloader/icon/identimetricsdownloader.png)

#### Note
This application is not affiliated in any way with Identimetrics, Inc.
