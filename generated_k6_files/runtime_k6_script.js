import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: `${__ENV.RAMP_UP || '10'}s`, target: parseInt(__ENV.VUS || '10') },
    { duration: `${__ENV.DURATION || '30'}s`, target: parseInt(__ENV.VUS || '10') },
  ],
};

let bearer_token = __ENV.BEARER_TOKEN || '';
let agent_id = '';
let prompt_id = '';
let status = '';

export default function () {
  // TC_01_save_draft
  let saveDraftRes = http.post(
    'https://agentflow-dev.tigeranalyticstest.in/aiapi/agents/save_draft',
    JSON.stringify({
      agent_architecture: {
        nodes: [
          {
            id: 'b1a78bfb-c054-4d47-8909-74b95e889728',
            type: 'core_node',
            position: { x: -266.28417309847737, y: 423.41652471368974 },
            data: {
              color: '#2BA7E0',
              name: 'Start',
              node_type: 'chat_input',
              node_family: 'system',
              disableInput: false,
              disableOutput: false,
              form: { history_context_length: 5 },
              input_keys: [],
            },
            deletable: false,
          },
          {
            id: 'd7b91222-fd51-4c4a-ae46-7ad9708e48a6',
            type: 'core_node',
            position: { x: 1509.6249178106134, y: 438.9922822894472 },
            data: {
              color: '#4070F5',
              name: 'End',
              node_type: 'chat_output',
              node_family: 'system',
              disableInput: false,
              disableOutput: false,
              form: {},
            },
            deletable: false,
          },
        ],
        edges: [],
      },
      canvas_version: '1.0.1',
      name: 'Agent_tempaugest001',
      description: '',
      source: 'Manual',
      agent_framework: 'langgraph',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${bearer_token}`,
      },
    }
  );

  check(saveDraftRes, {
    'TC_01_save_draft: Status is 200': (r) => r.status === 200,
    'TC_01_save_draft: Message is correct': (r) =>
      r.json('message') === 'Agent Created & Secured',
  });

  agent_id = saveDraftRes.json('data.agent_id');

  // TC_02_create_draft
  let createDraftRes = http.post(
    'https://agentflow-dev.tigeranalyticstest.in/aiapi/agents/create_draft',
    JSON.stringify({
      agent_id: agent_id,
      is_first_version: true,
      source_agent_uuid: 'test',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${bearer_token}`,
      },
    }
  );

  check(createDraftRes, {
    'TC_02_create_draft: Status is 201': (r) => r.status === 201,
  });

  prompt_id = createDraftRes.json('data[0].prompt_id');
  status = createDraftRes.json('status');

  // TC_03_update_agent
  let updateAgentRes = http.put(
    'https://agentflow-dev.tigeranalyticstest.in/aiapi/agents/update',
    JSON.stringify({
      agent_id: agent_id,
      name: 'Agent_renamed',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${bearer_token}`,
      },
    }
  );

  check(updateAgentRes, {
    'TC_03_update_agent: Status is 200': (r) => r.status === 200,
  });

  // TC_04_save_draft_update
  let saveDraftUpdateRes = http.post(
    'https://agentflow-dev.tigeranalyticstest.in/aiapi/agents/save_draft',
    JSON.stringify({
      agent_architecture: {
        nodes: [
          {
            id: 'b1a78bfb-c054-4d47-8909-74b95e889728',
            type: 'core_node',
            position: { x: -266.28417309847737, y: 423.41652471368974 },
            data: {
              color: '#2BA7E0',
              name: 'Start',
              node_type: 'chat_input',
              node_family: 'system',
              disableInput: false,
              disableOutput: false,
              form: { history_context_length: 5 },
              input_keys: [],
            },
            deletable: false,
          },
          {
            id: 'd7b91222-fd51-4c4a-ae46-7ad9708e48a6',
            type: 'core_node',
            position: { x: 1509.6249178106134, y: 438.9922822894472 },
            data: {
              color: '#4070F5',
              name: 'End',
              node_type: 'chat_output',
              node_family: 'system',
              disableInput: false,
              disableOutput: false,
              form: {},
            },
            deletable: false,
          },
        ],
        edges: [],
      },
      canvas_version: '1.0.1',
      name: 'Agent_tempaugest001',
      description: '',
      source: 'Manual',
      agent_framework: 'langgraph',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  check(saveDraftUpdateRes, {
    'TC_04_save_draft_update: Status is 200': (r) => r.status === 200,
    'TC_04_save_draft_update: Message is correct': (r) =>
      r.json('message') === 'Agent Updated Successfully',
  });

  // TC005_Prompts_Clone
  let promptsCloneRes = http.post(
    'https://agentflow-dev.tigeranalyticstest.in/aiapi/prompts/clone',
    JSON.stringify({
      source_prompt_id: prompt_id,
      prompt_name: `cloned_${Math.random().toString(36).substring(2, 4)}`,
      version: '1.0',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${bearer_token}`,
      },
    }
  );

  check(promptsCloneRes, {
    'TC005_Prompts_Clone: Status is 200': (r) => r.status === 200,
  });

  sleep(1);
}