from locust import HttpUser, task, between
                import urllib3

                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                class LocustApiUser(HttpUser):
                    wait_time = between(1, 3)
                
                    @task
                    def api_task_1(self):
                        headers = "application/json"
                        payload = "{ \n\"agent_architecture\":{ \n\"nodes\":[ \n{ \n\"id\":\"b1a78bfb-c054-4d47-8909-74b95e889728\", \n\"type\":\"core_node\", \n\"position\":{ \n\"x\":-266.28417309847737, \n\"y\":423.41652471368974 \n}, \n\"data\":{ \n\"color\":\"#2BA7E0\", \n\"name\":\"Start\", \n\"node_type\":\"chat_input\", \n\"node_family\":\"system\", \n\"disableInput\":false, \n\"disableOutput\":false, \n\"form\":{ \n\"history_context_length\":5 \n}, \n\"input_keys\":[] \n}, \n\"deletable\":false \n}, \n{ \n\"id\":\"d7b91222-fd51-4c4a-ae46-7ad9708e48a6\", \n\"type\":\"core_node\", \n\"position\":{ \n\"x\":1509.6249178106134, \n\"y\":438.9922822894472 \n}, \n\"data\":{ \n\"color\":\"#4070F5\", \n\"name\":\"End\", \n\"node_type\":\"chat_output\", \n\"node_family\":\"system\", \n\"disableInput\":false, \n\"disableOutput\":false, \n\"form\":{} \n}, \n\"deletable\":false \n} \n], \n\"edges\":[] \n}, \n\"canvas_version\":\"1.0.1\", \n\"name\":\"Agent_tempaugest001\", \n\"description\":\"\", \n\"source\":\"Manual\", \n\"agent_framework\":\"langgraph\" \n}"
                        self.client.request("POST", "/aiapi/agents/save_draft", headers=headers, json=payload if "POST" in ["POST", "PUT", "PATCH"] else None, verify=False)
                
                    @task
                    def api_task_2(self):
                        headers = "application/json"
                        payload = "{\n  \"agent_id\": \"${agent_id}\",\n  \"is_first_version\": true,\n  \"source_agent_uuid\": \"test\"\n}"
                        self.client.request("POST", "/aiapi/agents/create_draft", headers=headers, json=payload if "POST" in ["POST", "PUT", "PATCH"] else None, verify=False)
                
                    @task
                    def api_task_3(self):
                        headers = "application/json"
                        payload = "{\n  \"agent_id\": \"${agent_id}\",\n  \"name\": \"Agent_renamed\"\n}"
                        self.client.request("PUT", "/aiapi/agents/update", headers=headers, json=payload if "PUT" in ["POST", "PUT", "PATCH"] else None, verify=False)
                
                    @task
                    def api_task_4(self):
                        headers = "application/json"
                        payload = "{\n  \"agent_architecture\": {\n    \"nodes\": [\n      {\n        \"id\": \"b1a78bfb-c054-4d47-8909-74b95e889728\",\n        \"type\": \"core_node\",\n        \"position\": {\n          \"x\": -266.28417309847737,\n          \"y\": 423.41652471368974\n        },\n        \"data\": {\n          \"color\": \"#2BA7E0\",\n          \"name\": \"Start\",\n          \"node_type\": \"chat_input\",\n          \"node_family\": \"system\",\n          \"disableInput\": false,\n          \"disableOutput\": false,\n          \"form\": {\n            \"history_context_length\": 5\n          },\n          \"input_keys\": []\n        },\n        \"deletable\": false\n      },\n      {\n        \"id\": \"d7b91222-fd51-4c4a-ae46-7ad9708e48a6\",\n        \"type\": \"core_node\",\n        \"position\": {\n          \"x\": 1509.6249178106134,\n          \"y\": 438.9922822894472\n        },\n        \"data\": {\n          \"color\": \"#4070F5\",\n          \"name\": \"End\",\n          \"node_type\": \"chat_output\",\n          \"node_family\": \"system\",\n          \"disableInput\": false,\n          \"disableOutput\": false,\n          \"form\": {}\n        },\n        \"deletable\": false\n      }\n    ],\n    \"edges\": []\n  },\n  \"canvas_version\": \"1.0.1\",\n  \"name\": \"Agent_tempaugest001\",\n  \"description\": \"\",\n  \"source\": \"Manual\",\n  \"agent_framework\": \"langgraph\"\n}"
                        self.client.request("POST", "/aiapi/agents/save_draft", headers=headers, json=payload if "POST" in ["POST", "PUT", "PATCH"] else None, verify=False)
                
                    @task
                    def api_task_5(self):
                        headers = "application/json"
                        payload = "{\n  \"source_prompt_id\": \"${prompt_id}\",\n  \"prompt_name\": \"cloned_${__RandomString(2,abcdefghijklmnopqrstuvwxyz,)}\",\n  \"version\": \"1.0\"\n}"
                        self.client.request("POST", "/aiapi/prompts/clone", headers=headers, json=payload if "POST" in ["POST", "PUT", "PATCH"] else None, verify=False)
                
                