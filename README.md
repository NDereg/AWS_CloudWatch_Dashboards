# Python 3.6
## Update CloudWatch Dashboard
The following code is intended to be used as a Lambda function. The Lambda function will automatically maintain and update the following CloudWatch dashboards; *NA-Dash*, *EU-Dash*, *AU-Dash*. Lambda can be triggered by a CloudWatch Event.


## Instructions
- Clone this repository.
- Optional:
  - Assuming you have gitlab-ci setup; when committing code to **any** branch, `./.gitlab-ci.yml` will automatically update the Lambda function.
- When modifying in the event of adding new *widgets*, the following are **required** to be updated due to CloudWatch Dashboards **source** being structured differently: `./data/config.json`, `./data/dashboard.json`, `./lib/cw_dashboard.py`


## Structure Overview
- Folders
  - `./vscode/`: vscode, project workspace settings.
  - `./lib`: contains the project's main code.
  - `./data`: contains data files.
  - `./scripts`: debug scripts.
- Files
  - `config.json`: data file containing resource names.
  - `dashboard.json`: CloudWatch dashboard source structure.
  - `cw_dashboard.py`: main project code.
  - `handler.py`: lambda handler that calls cw_dashboard.py.