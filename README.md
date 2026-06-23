### Tiger QE AI Accelerator! 🚀 Your Gateway to Smarter Testing!

# Gen-AI Accelerators

## Prerequisites

* Python 3.x installed
* UV (Unified Virtual Environment) installed
* Streamlit package installed within the environment

## Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/lokeshwaranamir/ai-accelerator.git
   ```

2. **Activate the Virtual Environment:**

   ```bash
   uv activate .venv
   ```

3. **Install Required Packages:**

   ```bash
   pip install -r pyproject.toml
   ```

4. **Run the Streamlit Application:**

   ```bash
   streamlit run accelerator/Gen-AI-Accelerators.py
   ```

## Access the Application

After running the above command, the Streamlit application will be available at:

```
http://localhost:8501
```
## Db Integeration
 Please run database_utils/init_db.py - to create db session and create required table
 run database_utils/Prompt_list.py - to add the prompts to the table 
 Open the config/setting.ini file and chnage the source to 'database' from 'file'
 Now run the action_new_xpath.py'
```
http://localhost:8501
## Troubleshooting

* Ensure that the virtual environment is activated before running the Streamlit command.
* If the package is not found, verify the environment name or check if the required packages are installed.


## Sample Prompt for Demo
As a customer, I want all sign-in/updates to primary address in profile to also update the global shipping zip code. So I can seamlessly log-in to my account and have my preferred address be the basis for all default shipping information. Acceptance Criteria: If a primary address is present then the any of these account events must update the global ship zip Sign-In Edit and Save of current primary address Switch to new primary address If a primary address is not associated with the account then no action will be taken Updates to global ship zip manually elsewhere on the site will not update the primary address

